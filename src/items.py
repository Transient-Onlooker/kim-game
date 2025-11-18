import pygame
import random
from config import *
from utils import load_image

# 이 파일은 코인, 포션 등 플레이어가 수집하거나 사용하는 아이템들의 클래스를 관리합니다.

class Coin(pygame.sprite.Sprite):
    def __init__(self, center_pos):
        super().__init__()
        
        # 코인 이미지 로드 및 크기 조절
        self.image = load_image("src/assets/images/coin.png", scale=(20, 20))
        self.rect = self.image.get_rect(center=center_pos)
        self.pos = pygame.math.Vector2(center_pos)
        
        # 코인의 가치 (나중에 보스 코인 등을 위해 확장 가능)
        self.value = 10
        
        # 생성 시간 및 소멸 시간
        self.spawn_time = pygame.time.get_ticks()
        self.lifespan = 5000 # 5초

    def update(self):
        # 생성 후 5초가 지나면 스스로를 그룹에서 제거 (소멸)
        if pygame.time.get_ticks() - self.spawn_time > self.lifespan:
            self.kill()