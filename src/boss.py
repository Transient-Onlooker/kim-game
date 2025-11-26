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
        multiplier = 1.8 ** (stage_level - 1)
        self.hp = self.stats['hp'] * multiplier
        self.max_hp = self.stats['hp'] * multiplier
        self.attack_power = self.stats['attack_power'] * multiplier
        self.move_speed = self.stats['move_speed']
        
        # 이미지 및 애니메이션 설정
        self.animation_frames = []
        self.animation_speed = 300 # 0.3초마다 프레임 변경
        
        if self.enemy_key == 'fire_boss':
            self.animation_frames.append(load_image('src/assets/images/fire_boss_1.png', scale=(180, 180)))
            self.animation_frames.append(load_image('src/assets/images/fire_boss_2.png', scale=(180, 180)))
        elif self.enemy_key == 'poison_boss':
            self.animation_frames.append(load_image('src/assets/images/poison_boss_1.png', scale=(180, 180)))
            self.animation_frames.append(load_image('src/assets/images/poison_boss_2.png', scale=(180, 180)))
        elif self.enemy_key == 'void_boss':
            self.animation_frames.append(load_image('src/assets/images/void_boss_1.png', scale=(180, 180)))
            self.animation_frames.append(load_image('src/assets/images/void_boss_2.png', scale=(180, 180)))

        if self.animation_frames:
            self.current_frame_index = 0
            self.image = self.animation_frames[self.current_frame_index]
            self.last_animation_time = pygame.time.get_ticks()
        else:
            # 애니메이션 프레임이 없는 경우, 기존 방식대로 단일 이미지 로드
            image_path = f"src/assets/images/{boss_key}.png"
            self.image = load_image(image_path, scale=(180, 180))
            
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
        self.animate()

    def animate(self):
        """애니메이션 프레임을 업데이트합니다."""
        if not self.animation_frames:
            return

        now = pygame.time.get_ticks()
        if now - self.last_animation_time > self.animation_speed:
            self.last_animation_time = now
            self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_frames)
            self.image = self.animation_frames[self.current_frame_index]

    def draw(self, surface):
        surface.blit(self.image, self.rect)
