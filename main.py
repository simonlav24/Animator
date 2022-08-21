from vector import *
from math import radians
import PsdLoader
import pygame

pygame.init()

win = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
artBoard = pygame.Surface((512, 512), pygame.SRCALPHA)
artBoardPos = Vector(win.get_width() // 2 - artBoard.get_width() // 2, win.get_height() // 2 - artBoard.get_height() // 2)
clock = pygame.time.Clock()
fps = 60

keyFrameDiamond = [(2,0),(0,4),(-2,0),(0,-4)]

class Display:
    _instance = None
    def __init__(self):
        Display._instance = self
        self.timeLine = TimeLine(5)
        self.selectedHandle = None
        self.selectedObj = None
        # self.attributes = Attributes()
    def getInstance():
        return Display._instance
    def handleEvents(self, event):
        # mouse pressed
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # if timeline selected
            if TimeLine._instance.state == TIMELINE_PAUSE:
                if TimeLine._instance.selected:
                    TimeLine._instance.state = TIMELINE_DRAG
            if self.selectedHandle:
                Handle._state = "drag"
        # mouse released
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            # if timeline selected
            if TimeLine._instance.state == TIMELINE_DRAG:
                TimeLine._instance.state = TIMELINE_PAUSE
                self.updateHandles()
            if Handle._state == "drag":
                Handle._state = "idle"
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.timeLine.togglePlay()
                self.updateHandles()
    def updateHandles(self):
        if self.selectedObj:
            Handle.createHandles(self.selectedObj)
    def step(self):
        self.timeLine.step()
        for h in Handle._reg:
            h.step()
        if self.selectedHandle:
            if Handle._state == "idle":
                if not distus(self.selectedHandle.pos, pygame.mouse.get_pos()) < Handle._radius * Handle._radius:
                    self.selectedHandle.selected = False
                    self.selectedHandle = None
            elif Handle._state == "drag":
                self.selectedHandle.update()
    def draw(self):
        self.timeLine.draw()
        for h in Handle._reg:
            h.draw()

class Attributes:
    _instance = None
    def __init__(self):
        Attributes._instance = self
        self.surf = pygame.Surface((512, win.get_width() // 2))
    def handleEvents(self, event):
        pass
    def step(self):
        pass
    def draw(self):
        win.blit(self.surf, (win.get_width() - self.surf.get_width(), win.get_height() // 2))

class KeyValue:
    def __init__(self, frame, value, slope=1):
        self.frame = frame
        self.value = value
        self.slope = slope
    def __str__(self):
        return "KeyValue(" + str(self.frame) + ", " + str(self.value) + ")"
    def __repr__(self):
        return self.__str__()

class Shape:
    def __init__(self, pos):
        self.initialize(pos)
    def initialize(self, pos):
        self.pos = vectorCopy(pos)
        self.keyFrames = {}
        self.children = []
        self.parent = None
    def move(self, pos, abs=False):
        if abs:
            self.pos = pos
        else:
            self.pos += pos
        # for child in self.children:
        #     child.move(pos, abs)
    def rotate(self, angle, abs=False):
        pass
    def getParentPos(self):
        if self.parent == None:
            return Vector()
        return self.parent.pos
    def addChild(self, child):
        posOfChild = child.pos - self.pos
        self.children.append(child)
        child.parent = self
        child.move(posOfChild, abs=True)
    def getSize(self):
        pass
    def addKeyFrame(self, frame, key, value, slope=1):
        k = KeyValue(frame, value, slope)
        if key in self.keyFrames:
            self.keyFrames[key].append(k)
        else:
            self.keyFrames[key] = [k]
        # sort the keyframes by frame
        self.keyFrames[key].sort(key=lambda x: x.frame)
    def evaluateKeyframes(self):
        currentFrame = Display.getInstance().timeLine.getCurrentFrame()
        currentKeys = {}
        for key in self.keyFrames.keys():
            list = self.keyFrames[key]
            # find the first keyframe that is greater than currentFrame
            if len(list) == 0:
                continue
                
            low, high = self.binary_search(list, currentFrame)
            currentKeys[key] = (low, high)
        return currentKeys

    def binary_search(self, list, target):
        low = 0
        high = len(list) - 1
        while low < high:
            if abs(low - high) == 1:
                if target < list[low].frame:
                    return (None, list[low])
                if target > list[high].frame:
                    return (list[high], None)
                return (list[low], list[high])
            mid = (low + high) // 2
            if target > list[mid].frame:
                low = mid
            elif target < list[mid].frame:
                high = mid
            else:
                return (list[mid], list[high])
        
        highKey = None if high == len(list) - 1 else list[high]
        lowKey = None if low == 0 else list[low]
        return (lowKey, highKey)

    def performKeyframes(self, currentKeys):
        for key in currentKeys.keys():
            if key == "pos":
                newPos = self.keyframeInterpolate(currentKeys[key][0], currentKeys[key][1])
                if not newPos:
                    continue
                self.move(newPos, abs=True)

    def keyframeInterpolate(self, key1, key2):
        if key1 == None and key2 == None:
            return None
        if key1 == None:
            return key2.value
        if key2 == None:
            return key1.value
        frame = Display.getInstance().timeLine.getCurrentFrame()

        p0 = key1.slope
        p1 = key2.slope

        # interpolate according to the function y = (p1 -2 +p0)x^3 + (-p1+3-2p0)x^2 +p0x
        t = (frame - key1.frame) / (key2.frame - key1.frame)
        calculated_t = (p1 - 2 + p0) * t * t * t + (-p1 + 3 - 2 * p0) * t * t + p0 * t
        return key1.value + (key2.value - key1.value) * calculated_t
    def getAbsolutePos(self):
        if self.parent == None:
            return self.pos
        return self.parent.getAbsolutePos() + self.pos
    def step(self):
        if Display._instance.timeLine.state != TIMELINE_PAUSE:
            currentKeys = self.evaluateKeyframes()
            self.performKeyframes(currentKeys)
        for child in self.children:
            child.step()
        
    def draw(self):
        # might be wrong
        for child in self.children:
            child.draw()
        # draw keyframes
        for key in self.keyFrames.keys():
            list = self.keyFrames[key]
            for k in list:
                timeLine = TimeLine.getInstance()
                timeLine.drawKeyFrame(k)
                # pygame.draw.circle(artBoard, (255, 0, 0), (k.frame, k.value), 5)
class Circle(Shape):
    def __init__(self, pos, radius):
        self.initialize(pos)
        self.radius = radius
    def performKeyframes(self, currentKeys):
        super().performKeyframes(currentKeys)
        for key in currentKeys.keys():
            if key == "radius":
                self.radius = self.keyframeInterpolate(currentKeys[key][0], currentKeys[key][1])
    def draw(self):
        pos = self.getParentPos() + self.pos
        pygame.draw.circle(artBoard, (255, 255, 255), pos, self.radius)
        super().draw()

class RotatableShape(Shape):
    def __init__(self, pos, anchor=Vector(), angle=0):
        self.initialize(pos, anchor, angle)
    def initialize(self, pos, anchor=Vector(), angle=0):
        super().initialize(pos)
        self.anchor = anchor
        self.angle = angle
    def getParentAngle(self):
        if self.parent == None:
            return 0
        return self.parent.angle
    def setPosRel(self, vec):
        self.pos = self.pos + vec
    def setAnchor(self, vec):
        self.anchor = vec
        self.pos = self.pos + self.anchor
    def rotate(self, angle, abs=False):
        if abs:
            diff = angle - self.angle
            self.angle = angle
            for child in self.children:
                child.pos = rotateVector(child.pos, radians(-diff))
        else:
            # not tested yet
            self.angle += angle
            for child in self.children:
                child.pos -= self.pos
                child.pos.rotate(radians(self.angle))
                child.pos += self.pos
        
    def performKeyframes(self, currentKeys):
        super().performKeyframes(currentKeys)
        for key in currentKeys.keys():
            if key == "angle":
                self.rotate(self.keyframeInterpolate(currentKeys[key][0], currentKeys[key][1]), abs=True)
    def draw(self):
        super().draw()

class Surf(RotatableShape):
    def __init__(self, pos, surf):
        self.initialize(pos)
        self.orgSurf = surf
        self.surf = surf
    def setSize(self, size):
        self.surf = pygame.transform.scale(self.orgSurf, size)
    def getSize(self):
        return self.surf.get_size()
    def draw(self):
        angle = self.getParentAngle() + self.angle
        pos = self.getParentPos() + self.pos
        # surf = pygame.transform.rotate(self.surf, angle)
        surf = pygame.transform.rotozoom(self.surf, angle, 1.0)
        anchorTag = pos + self.anchor
        pos = pos - anchorTag
        pos.rotate(-radians(angle))
        pos = pos + anchorTag
        artBoard.blit(surf, (pos - self.anchor) - Vector(surf.get_width() // 2, surf.get_height() // 2))
        pygame.draw.circle(artBoard, (200,200,0), self.getAbsolutePos(), 2)
        super().draw()

class Handle:
    _radius = 5
    _reg = []
    _state = "idle"
    def __init__(self, obj, pos, mode):
        self.pos = tup2vec(pos)
        self.selected = False
        self.obj = obj
        self.mode = mode
    def step(self):
        mousePos = pygame.mouse.get_pos()
        if not Display._instance.selectedHandle and distus(mousePos, self.pos) < self._radius * self._radius:
            self.selected = True
            Display._instance.selectedHandle = self
    def draw(self):
        color = (255,255,255) if not self.selected else (0,255,0)
        # pygame.draw.circle(win, color, self.pos, self._radius, 1)
        pygame.draw.rect(win, color, (self.pos[0] - self._radius, self.pos[1] - self._radius, self._radius * 2, self._radius * 2))

    def updateHandles():
        pos = tup2vec(obj.getAbsolutePos()) + artBoardPos
        size = tup2vec(obj.getSize())
        Handle._reg[0].pos = pos - size // 2
        Handle._reg[1].pos = pos - Vector(0, size.y // 2)
        Handle._reg[2].pos = pos + Vector(size.x // 2 , -size.y // 2)
        Handle._reg[3].pos = pos - Vector(size.x // 2, 0)
        Handle._reg[4].pos = pos + Vector(size.x // 2, 0)
        Handle._reg[5].pos = pos + Vector(-size.x // 2, size.y // 2)
        Handle._reg[6].pos = pos + Vector(0, size.y // 2)
        Handle._reg[7].pos = pos + Vector(size.x // 2, size.y // 2)
        Handle._reg[8].pos = pos
    def createHandles(obj):
        # create 9 handles for the obj
        pos = tup2vec(obj.getAbsolutePos()) + artBoardPos
        size = tup2vec(obj.getSize())

        Handle._reg.clear()

        Handle._reg.append(Handle(obj, pos - size // 2, "tl"))
        Handle._reg.append(Handle(obj, pos - Vector(0, size.y // 2), "tm"))
        Handle._reg.append(Handle(obj, pos + Vector(size.x // 2 , -size.y // 2), "tr"))
        Handle._reg.append(Handle(obj, pos - Vector(size.x // 2, 0), "ml"))
        Handle._reg.append(Handle(obj, pos + Vector(size.x // 2, 0), "mr"))
        Handle._reg.append(Handle(obj, pos + Vector(-size.x // 2, size.y // 2), "bl"))
        Handle._reg.append(Handle(obj, pos + Vector(0, size.y // 2), "bm"))
        Handle._reg.append(Handle(obj, pos + Vector(size.x // 2, size.y // 2), "br"))
        Handle._reg.append(Handle(obj, pos, "c"))

    def update(self):
        mousePos = tup2vec(pygame.mouse.get_pos())
        objAbsPos = self.obj.getAbsolutePos() + artBoardPos
        self.pos = mousePos
        if self.mode == "c":
            obj.setPosRel(mousePos - objAbsPos)
            Handle.updateHandles()
        elif self.mode in ["tl", "tr", "bl", "br"]:
            newSize = (abs(objAbsPos.x - mousePos.x) * 2, abs(objAbsPos.y - mousePos.y) * 2)
            self.obj.setSize(newSize)
            Handle.updateHandles()
        elif self.mode in ["tm", "bm"]:
            newSize = (self.obj.getSize()[0], abs(objAbsPos.y - mousePos.y) * 2)
            self.obj.setSize(newSize)
            Handle.updateHandles()
        elif self.mode in ["ml", "mr"]:
            newSize = (abs(objAbsPos.x - mousePos.x) * 2, self.obj.getSize()[1])
            self.obj.setSize(newSize)
            Handle.updateHandles()

            



TIMELINE_PLAY = 0
TIMELINE_PAUSE = 1
TIMELINE_DRAG = 2

class TimeLine:
    animationFps = 25
    _instance = None
    def __init__(self, seconds):
        TimeLine._instance = self
        self.timeOverall = 0
        self.frameCount = 25 * seconds
        self.currentFrame = 0
        self.state = TIMELINE_PLAY
        self.selected = False
    def getInstance():
        return TimeLine._instance
    def frameToTime(frame):
        return (fps / TimeLine.animationFps) * frame

    def getCurrentFrame(self):
        return int((TimeLine.animationFps / fps) * self.timeOverall)
    def togglePlay(self):
        if self.state == TIMELINE_PLAY:
            self.state = TIMELINE_PAUSE
        else:
            self.state = TIMELINE_PLAY
    def restart(self):
        self.timeOverall = 0
        self.currentFrame = 0

    def step(self):
        mousePos = pygame.mouse.get_pos()
        seekerPos = self.getSeekerPosInWin(self.currentFrame)
        if distus(mousePos, seekerPos) < 10 * 10:
            self.selected = True
        else:
            self.selected = False
        
        if self.state == TIMELINE_PLAY:
            if self.timeOverall >= TimeLine.frameToTime(self.frameCount):
                self.timeOverall = 0
                self.currentFrame = 0

            self.currentFrame = int((TimeLine.animationFps / fps) * self.timeOverall)
            self.timeOverall += 1
        elif self.state == TIMELINE_PAUSE:
            pass
        elif self.state == TIMELINE_DRAG:
            mouseX = mousePos[0]
            currentFrame = int((mouseX - 50) / (win.get_width() - 100) * self.frameCount)
            if currentFrame < 0:
                currentFrame = 0
            elif currentFrame > self.frameCount:
                currentFrame = self.frameCount
            self.setCurrentFrame(currentFrame)
    def setCurrentFrame(self, frame):
        self.currentFrame = frame
        self.timeOverall = int(TimeLine.frameToTime(frame))
    def getSeekerPosInWin(self, frame):
        pos1 = Vector(50, win.get_height() - 50)
        pos2 = Vector(win.get_width() - 50, win.get_height() - 50)
        return pos1 + (pos2 - pos1) * (frame / self.frameCount)

    def drawKeyFrame(self, key):
        keyFramePos = self.getSeekerPosInWin(key.frame)
        # pygame.draw.circle(win, (255, 0, 0), keyFramePos, 2)
        pygame.draw.polygon(win, (255,255,0), [keyFramePos + tup2vec(i) for i in keyFrameDiamond])

    def draw(self):
        currentFramePos = self.getSeekerPosInWin(self.currentFrame)
        pos1 = Vector(50, win.get_height() - 50)
        pos2 = Vector(win.get_width() - 50, win.get_height() - 50)
        pygame.draw.line(win, (255, 255, 255), pos1, pos2)

        if self.selected or self.state == TIMELINE_DRAG:
            pygame.draw.circle(win, (255, 0, 0), currentFramePos, 8)
        pygame.draw.circle(win, (255, 255, 255), currentFramePos, 5)

# singleton renderer
class Renderer:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Renderer, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    def renderPNGSequance(self, path, name):
        timeline = TimeLine._instance
        frameCount = timeline.frameCount
        timeline.restart()
        for i in range(frameCount):
            timeline.step()
            for obj in objects:
                obj.step()
            artBoard.fill((0,0,0,0))
            for obj in objects:
                obj.draw()
            # save frame to path  with frame number with 4 digits
            pygame.image.save(artBoard, path + "/" + name + str(i).zfill(4) + ".png")
        timeline.restart()

# init
objects = []

def test1():

    c = Circle((100, 100), 50)
    objects.append(c)

    c.addKeyFrame(25, "pos", Vector(100,100))
    c.addKeyFrame(50, "pos", Vector(200,100))
    c.addKeyFrame(75, "pos", Vector(500,500))
    c.addKeyFrame(100, "pos", Vector(500,500))
    c.addKeyFrame(150, "pos", Vector(200,200))

    c.addKeyFrame(25, "radius", 10)
    c.addKeyFrame(50, "radius", 20)
    c.addKeyFrame(75, "radius", 10)
    c.addKeyFrame(100, "radius", 20)
    c.addKeyFrame(150, "radius", 10)

    s = Surf((300,300), pygame.image.load("D:/python/assets/anchor.png").convert_alpha())
    s.setAnchor(Vector(-45, 0))
    
    objects.append(s)
    s.addKeyFrame(25, "pos", Vector(100,100))
    s.addKeyFrame(50, "pos", Vector(200,100))
    s.addKeyFrame(75, "pos", Vector(500,500))
    s.addKeyFrame(100, "pos", Vector(500,500))
    s.addKeyFrame(150, "pos", Vector(200,200))

    s.addKeyFrame(0, "angle", 0)
    s.addKeyFrame(25 * 6, "angle", 360)

    s2 = Surf((200,300), pygame.image.load("D:/python/assets/blood3.png").convert_alpha())
    s.children.append(s2)

def test2():
    layers = PsdLoader.loadToLayers("D:\\python\\assets\\hand.psd")
    arm = Surf(layers[0][1], layers[0][0])
    arm.setAnchor(Vector(13, 30))
    objects.append(arm)
    hand = Surf(layers[1][1], layers[1][0])
    hand.setAnchor(Vector(-5, 80))
    
    arm.addChild(hand)
    # objects.append(hand)
    
    
    # arm.addKeyFrame(0, "pos", Vector(200,200))
    # arm.addKeyFrame(25, "pos", Vector(300,200))
    # arm.addKeyFrame(50, "pos", Vector(300,300))
    # arm.addKeyFrame(75, "pos", Vector(200,300))
    # arm.addKeyFrame(100, "pos", Vector(200,200))

    # arm.addKeyFrame(0, "angle", 0)
    # arm.addKeyFrame(25, "angle", -40)
    # arm.addKeyFrame(50, "angle", 0)

    # arm.addKeyFrame(0, "angle", 0)
    # arm.addKeyFrame(4*25, "angle", 360)

    # handPos = vectorCopy(hand.pos)

    hand.addKeyFrame(0, "angle", -20)
    hand.addKeyFrame(10, "angle", 20)
    hand.addKeyFrame(20, "angle", -20)
    hand.addKeyFrame(30, "angle", 20)
    hand.addKeyFrame(40, "angle", -20)
    hand.addKeyFrame(50, "angle", 20)
    hand.addKeyFrame(60, "angle", -20)
    hand.addKeyFrame(70, "angle", 20)
    hand.addKeyFrame(80, "angle", -20)
    hand.addKeyFrame(90, "angle", 20)
    hand.addKeyFrame(100, "angle", -20)
    hand.addKeyFrame(110, "angle", 20)

def test3():
    layers = PsdLoader.loadToLayers("D:\\python\\assets\\layertest2.psd")
    arm = Surf(layers[0][1], layers[0][0])
    arm.setAnchor(Vector(0, 0))
    objects.append(arm)
    arm2 = Surf(layers[1][1], layers[1][0])
    arm3 = Surf(layers[2][1], layers[2][0])
    objects.append(arm2)
    objects.append(arm3)
    # hand = Surf(layers[1][1], layers[1][0])
    
    arm.addKeyFrame(0, "angle", 0, 0)
    arm.addKeyFrame(25, "angle", 360,0)

    arm2.addKeyFrame(0, "angle", 0, 1)
    arm2.addKeyFrame(25, "angle", 360,1)

    arm3.addKeyFrame(0, "angle", 0, 3)
    arm3.addKeyFrame(25, "angle", 360, 3)

def testHandle():
    img = pygame.image.load("D:\\python\\assets\\hadi.png")
    hadi = Surf((100,100), img)
    objects.append(hadi)

    Display._instance.selectedObj = hadi
    Handle.createHandles(Display._instance.selectedObj)

display = Display()

testHandle()

r = Renderer()
r.renderPNGSequance('D:\\python\\assets\\testAnim', 'tester')

done = False
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        display.handleEvents(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pass
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                # set keyFrame temporary pos
                obj = display.selectedObj
                obj.addKeyFrame(display.timeLine.currentFrame, "pos", vectorCopy(obj.pos))

        
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        done = True

    # step
    display.step()
    # timeLine.step()

    # if timeLine.timeOverall == 60:
    #     objects[0].rotate(10)

    for obj in objects:
        obj.step()

    # draw
    win.fill((20, 20, 20))
    pygame.draw.rect(win, (0, 0, 0), (artBoardPos, artBoard.get_size()))
    win.blit(artBoard, artBoardPos)
    pygame.draw.rect(win, (255, 255, 255), (artBoardPos, artBoard.get_size()), 1)
    display.draw()
    artBoard.fill((0,0,0,0))
    # timeLine.draw()
    for obj in objects:
        obj.draw()
    
    

    pygame.display.update()
    clock.tick(fps)
pygame.quit()