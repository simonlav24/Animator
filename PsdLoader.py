import pygame
from psd_tools import PSDImage

def loadToLayers(path):
    psd = PSDImage.open(path)
    layers = []
    for layer in psd:
        image = layer.compose()
        # convert the image to a pygame surface
        surface = pygame.image.fromstring(image.tobytes(), image.size, image.mode)
        layers.append(surface)
    return layers