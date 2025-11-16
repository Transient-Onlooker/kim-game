import pygame
from config import *
import random

# 커스텀 이벤트 정의
STAGE_CLEAR = pygame.USEREVENT + 5

class Boss(pygame.sprite.Sprite):
    def __init__(self, boss_key, player, stage_level=1):
        super().__init__()
        
        self.stats = ENEMIES[boss_key].copy()
        
        # 스테이지 레벨에 따른 스탯 강화
        multiplier = 1.5 ** (stage_level - 1)
        self.hp = self.stats['hp'] * multiplier
        self.max_hp = self.stats['hp'] * multiplier
        self.attack_power = self.stats['attack_power'] * multiplier
        self.move_speed = self.stats['move_speed']
        
        # 이미지 및 위치 (크기를 더 크게 설정)
        try:
            # 보스 이미지 파일명이 boss_key와 같다고 가정 (예: fire_boss.png)
            image_path = f"src/assets/images/{boss_key}.png"
            original_image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(original_image, (120, 120)) # 크기 120x120
        except pygame.error as e:
            print(f"보스 이미지를 불러올 수 없습니다: {e}")
            self.image = pygame.Surface((120, 120))
            self.image.fill(RED)
            
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH / 2, 150)) # 화면 상단 중앙에서 등장
        self.pos = pygame.math.Vector2(self.rect.center)
        self.player = player

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.kill()
            pygame.event.post(pygame.event.Event(STAGE_CLEAR)) # 스테이지 클리어 이벤트 발생
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
