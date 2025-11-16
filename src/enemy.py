import pygame
import random
from config import *

class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_key, player, stage_level=1):
        super().__init__()
        
        # 적 스탯 설정
        self.stats = ENEMIES[enemy_key].copy() # 원본 딕셔너리 수정을 방지하기 위해 복사
        
        # 스테이지 레벨에 따른 스탯 강화
        multiplier = 1.5 ** (stage_level - 1)
        self.hp = self.stats['hp'] * multiplier
        self.max_hp = self.stats['hp'] * multiplier
        self.attack_power = self.stats['attack_power'] * multiplier
        self.move_speed = self.stats['move_speed'] # 이동 속도는 고정
        self.exp = self.stats['exp'] * multiplier
        
        # 이미지 및 위치
        try:
            image_path = f"src/assets/images/{enemy_key}.png"
            original_image = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(original_image, (40, 40)) # 이미지 크기 통일
        except pygame.error as e:
            print(f"적 이미지를 불러올 수 없습니다: {e}")
            self.image = pygame.Surface((40, 40))
            self.image.fill(RED)
        
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            x = random.randint(0, SCREEN_WIDTH)
            y = -self.image.get_height()
        elif side == 'bottom':
            x = random.randint(0, SCREEN_WIDTH)
            y = SCREEN_HEIGHT
        elif side == 'left':
            x = -self.image.get_width()
            y = random.randint(0, SCREEN_HEIGHT)
        else: # 'right'
            x = SCREEN_WIDTH
            y = random.randint(0, SCREEN_HEIGHT)
            
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos = pygame.math.Vector2(self.rect.topleft)
        self.player = player

    def take_damage(self, amount):
        """적이 데미지를 입었을 때 호출됩니다."""
        self.hp -= amount
        if self.hp <= 0:
            self.kill() # 체력이 0 이하면 스스로를 그룹에서 제거
            return self.exp # 플레이어에게 줄 경험치 반환
        return 0 # 아직 살아있으면 0 반환

    def update(self):
        """적의 상태 업데이트 (플레이어 추적)"""
        direction = pygame.math.Vector2(self.player.rect.center) - self.pos
        
        if direction.length() > 0:
            direction.normalize_ip()
            self.pos += direction * self.move_speed
        
        self.rect.topleft = self.pos

    def draw(self, surface):
        """적을 화면에 그림"""
        surface.blit(self.image, self.rect)
