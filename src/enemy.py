import pygame
import random
from config import *
from utils import load_image

class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_key, player, stage_level=1):
        super().__init__()
        
        self.enemy_key = enemy_key # 적 종류를 식별하기 위한 키 저장
        
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
        image_path = f"src/assets/images/{enemy_key}.png"
        self.image = load_image(image_path, scale=(40, 40))
        
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

    def draw_health_bar(self, surface):
        """적 개체 위에 체력 바를 그립니다."""
        if self.hp < self.max_hp: # 최대 체력일 때는 그리지 않음
            bar_width = 40
            bar_height = 5
            x = self.rect.x
            y = self.rect.y - bar_height - 2 # 적 이미지 위에 약간의 간격을 둠

            health_ratio = self.hp / self.max_hp
            
            # 배경 바 (회색)
            bg_rect = pygame.Rect(x, y, bar_width, bar_height)
            pygame.draw.rect(surface, GRAY, bg_rect)
            
            # 체력 바 (빨간색)
            health_rect = pygame.Rect(x, y, bar_width * health_ratio, bar_height)
            pygame.draw.rect(surface, RED, health_rect)
            
            # 테두리 (흰색)
            pygame.draw.rect(surface, WHITE, bg_rect, 1)

    def draw(self, surface):
        """적을 화면에 그림"""
        surface.blit(self.image, self.rect)
