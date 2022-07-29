from vector import *
from math import radians
import pygame

pygame.init()
win = pygame.display.set_mode((1280, 720))
artBoard = pygame.Surface((512, 512), pygame.SRCALPHA)
clock = pygame.time.Clock()
fps = 60

class KeyValue:
    def __init__(self, frame, value):
        self.frame = frame
        self.value = value
    def __str__(self):
        return "KeyValue(" + str(self.frame) + ", " + str(self.value) + ")"
    def __repr__(self):
        return self.__str__()

class Shape:
    def __init__(self, pos):
        self.pos = pos
        self.initialize()
    def initialize(self):
        self.keyFrames = {}
    def addKeyFrame(self, frame, key, value):
        k = KeyValue(frame, value)
        if key in self.keyFrames:
            self.keyFrames[key].append(k)
        else:
            self.keyFrames[key] = [k]
        # sort the keyframes by frame
        self.keyFrames[key].sort(key=lambda x: x.frame)
    def evaluateKeyframes(self):
        currentFrame = timeLine.getCurrentFrame()
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
        if target == 51:
            x = 0
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
        pass

    def keyframeInterpolate(self, key1, key2):
        if key1 == None and key2 == None:
            return None
        if key1 == None:
            return key2.value
        if key2 == None:
            return key1.value
        # if key1.frame == key2.frame:
        currentFrame = timeLine.getCurrentFrame()
        # interpolate between key1 and key2
        # if currentFrame == key1.frame:
        #     return key1.value
        # if currentFrame == key2.frame:
        #     return key2.value
        return key1.value + (key2.value - key1.value) * (currentFrame - key1.frame) / (key2.frame - key1.frame)


    def step(self):
        currentKeys = self.evaluateKeyframes()
        self.performKeyframes(currentKeys)
        

    def draw(self):
        pass

class Circle(Shape):
    def __init__(self, pos, radius):
        self.initialize()
        self.pos = pos
        self.radius = radius
    def performKeyframes(self, currentKeys):
        for key in currentKeys.keys():
            if key == "radius":
                self.radius = self.keyframeInterpolate(currentKeys[key][0], currentKeys[key][1])
            elif key == "pos":
                self.pos = self.keyframeInterpolate(currentKeys[key][0], currentKeys[key][1])
    def draw(self):
        pygame.draw.circle(artBoard, (255, 255, 255), self.pos, self.radius)

class Surf(Shape):
    def __init__(self, pos, surf):
        self.initialize()
        self.pos = pos
        self.surf = surf
        self.anchor = Vector(0, 0)
        self.rotation = 30
    def performKeyframes(self, currentKeys):
        for key in currentKeys.keys():
            if key == "pos":
                self.pos = self.keyframeInterpolate(currentKeys[key][0], currentKeys[key][1])
            elif key == "rotation":
                self.rotation = self.keyframeInterpolate(currentKeys[key][0], currentKeys[key][1])
    def draw(self):
        # self.rotation = 30
        surf = pygame.transform.rotate(self.surf, self.rotation)
        anchorTag = self.pos + self.anchor
        pos = self.pos - anchorTag
        pos.rotate(-radians(self.rotation))
        pos = pos + anchorTag
        artBoard.blit(surf, pos - self.anchor - Vector(surf.get_width() // 2, surf.get_height() // 2))

class TimeLine:
    animationFps = 25
    def __init__(self):
        self.timeOverall = 0
        self.frameCount = 25 * 6
        self.currentFrame = 0
    
    # @staticmethod
    def frameToTime(frame):
        return (fps / TimeLine.animationFps) * frame

    def getCurrentFrame(self):
        return int((TimeLine.animationFps / fps) * self.timeOverall)

    def restart(self):
        self.timeOverall = 0
        self.currentFrame = 0

    def step(self):
        if self.timeOverall >= TimeLine.frameToTime(self.frameCount):
            self.timeOverall = 0
            self.currentFrame = 0

        self.currentFrame = int((TimeLine.animationFps / fps) * self.timeOverall)
        self.timeOverall += 1
        
    def draw(self):
        pos1 = Vector(50, win.get_height() - 50)
        pos2 = Vector(win.get_width() - 50, win.get_height() - 50)

        currentFramePos = pos1 + (pos2 - pos1) * (self.currentFrame / self.frameCount)
        pygame.draw.line(win, (255, 255, 255), pos1, pos2)
        pygame.draw.circle(win, (255, 255, 255), currentFramePos, 5)

# singleton renderer
class Renderer:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Renderer, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    def renderPNGSequance(self, path, name):
        frameCount = timeLine.frameCount
        timeLine.restart()
        for i in range(frameCount):
            timeLine.step()
            for obj in objects:
                obj.step()
            artBoard.fill((0,0,0,0))
            for obj in objects:
                obj.draw()
            # save frame to path  with frame number with 4 digits
            pygame.image.save(artBoard, path + "/" + name + str(i).zfill(4) + ".png")
        timeLine.restart()

objects = []

# init
timeLine = TimeLine()

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

s = Surf((400,400), pygame.image.load("D:/python/assets/anchor.png").convert_alpha())
# s.anchor = Vector(-45, 0)
objects.append(s)
s.addKeyFrame(25, "pos", Vector(100,100))
s.addKeyFrame(50, "pos", Vector(200,100))
s.addKeyFrame(75, "pos", Vector(500,500))
s.addKeyFrame(100, "pos", Vector(500,500))
s.addKeyFrame(150, "pos", Vector(200,200))

s.addKeyFrame(0, "rotation", 0)
s.addKeyFrame(25 * 6, "rotation", 360)

r = Renderer()
r.renderPNGSequance('D:\\python\\assets\\testAnim', 'tester')

done = False
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        done = True

    # step
    timeLine.step()
    for obj in objects:
        obj.step()

    # draw
    win.fill((20, 20, 20))
    artBoard.fill((0,0,0,0))
    
    timeLine.draw()
    for obj in objects:
        obj.draw()
    
    pygame.draw.rect(win, (0, 0, 0), (win.get_width() // 2 - artBoard.get_width() // 2, win.get_height() // 2 - artBoard.get_height() // 2, artBoard.get_width(), artBoard.get_height()))
    win.blit(artBoard, (win.get_width() // 2 - artBoard.get_width() // 2, win.get_height() // 2 - artBoard.get_height() // 2))
    pygame.draw.rect(win, (255, 255, 255), (win.get_width() // 2 - artBoard.get_width() // 2, win.get_height() // 2 - artBoard.get_height() // 2, artBoard.get_width(), artBoard.get_height()), 1)

    pygame.display.update()
    clock.tick(fps)
pygame.quit()