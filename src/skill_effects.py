# skill_effects.py
import pygame
from config import *

class SkillEffect(pygame.sprite.Sprite):
    def __init__(self, x, y, radius, damage, duration, color):
        super().__init__()
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius)
        self.rect = self.image.get_rect(center=(x, y))
        self.damage = damage
        self.duration = duration
        self.start_time = pygame.time.get_ticks()

    def update(self):
        if pygame.time.get_ticks() - self.start_time > self.duration:
            self.kill()

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, speed, damage, image_path):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (20, 20)) # Adjust size as needed
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.math.Vector2(x, y)
        self.target = pygame.math.Vector2(target_x, target_y)
        self.speed = speed
        self.damage = damage
        self.velocity = (self.target - self.pos).normalize() * self.speed

    def update(self):
        self.pos += self.velocity
        self.rect.center = self.pos
        # Remove projectile if it goes off screen
        if not SCREEN_RECT.colliderect(self.rect): # SCREEN_RECT is not defined here, will need to add it to config or pass it
            self.kill()

class AreaAttackEffect(pygame.sprite.Sprite):
    def __init__(self, x, y, radius, damage, duration, color=RED):
        super().__init__()
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (radius, radius), radius, 5) # Draw a circle outline
        self.rect = self.image.get_rect(center=(x, y))
        self.damage = damage
        self.duration = duration
        self.start_time = pygame.time.get_ticks()
        self.has_damaged = False # Ensure damage is applied only once

    def update(self):
        if pygame.time.get_ticks() - self.start_time > self.duration:
            self.kill()
