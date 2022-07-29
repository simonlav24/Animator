import pygame
from psd_tools import PSDImage

def loadToLayers(path):
    psd = PSDImage.open(path)
    layers = []
    for layer in psd:
        image = layer.compose()
        # position as center of bounding box
        width = layer.bbox[2] - layer.bbox[0]
        height = layer.bbox[3] - layer.bbox[1]
        x = layer.bbox[0] + width // 2
        y = layer.bbox[1] + height // 2

        layerPos = (x, y)
        # convert the image to a pygame surface
        surface = pygame.image.fromstring(image.tobytes(), image.size, image.mode)
        layers.append((surface, layerPos))
    return layers