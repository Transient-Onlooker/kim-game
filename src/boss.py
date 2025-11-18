import pygame
from config import *
from utils import load_image
import random

# 커스텀 이벤트 정의
STAGE_CLEAR = pygame.USEREVENT + 5

class Boss(pygame.sprite.Sprite):
    def __init__(self, boss_key, player, stage_level=1):
        super().__init__()
        
        self.enemy_key = boss_key # 보스 키 저장
        self.stats = ENEMIES[boss_key].copy()
        
        # 스테이지 레벨에 따른 스탯 강화
        multiplier = 1.5 ** (stage_level - 1)
        self.hp = self.stats['hp'] * multiplier
        self.max_hp = self.stats['hp'] * multiplier
        self.attack_power = self.stats['attack_power'] * multiplier
        self.move_speed = self.stats['move_speed']
        
        # 이미지 및 위치 (크기를 더 크게 설정)
        image_path = f"src/assets/images/{boss_key}.png"
        self.image = load_image(image_path, scale=(120, 120))
            
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH / 2, 150)) # 화면 상단 중앙에서 등장
        self.pos = pygame.math.Vector2(self.rect.center)
        self.player = player

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            # 스테이지 클리어 이벤트에 'boss' 객체(self)를 포함하여 전달
            stage_clear_event = pygame.event.Event(STAGE_CLEAR, {"boss": self})
            pygame.event.post(stage_clear_event)
            self.kill()
            return 0 # 보스는 경험치를 주지 않음
        return 0

    def update(self):
        direction = pygame.math.Vector2(self.player.rect.center) - self.pos
        if direction.length() > 0:
            direction.normalize_ip()
            self.pos += direction * self.move_speed
        self.rect.center = self.pos

    def draw(self, surface):
        surface.blit(self.image, self.rect)
