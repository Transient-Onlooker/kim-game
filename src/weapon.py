import pygame
import math
from config import *

class Weapon(pygame.sprite.Sprite):
    def __init__(self, player, enemies):
        super().__init__()
        
        self.player = player
        self.enemies = enemies
        
        # 무기 초기화 (간단한 사각형)
        self.image = pygame.Surface((15, 15))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect(center=player.rect.center)
        
        # 가장 가까운 적을 타겟으로 설정
        self.target = self.get_closest_enemy()
        
        # 타겟이 있을 경우, 해당 방향으로 속도 설정
        if self.target:
            direction = pygame.math.Vector2(self.target.rect.center) - pygame.math.Vector2(self.player.rect.center)
            if direction.length() > 0:
                self.velocity = direction.normalize() * 15 # 발사체 속도
            else:
                self.velocity = pygame.math.Vector2(0, -1) * 15 # 적과 겹쳐있을 경우 위로 발사
        else:
            # 적이 없으면 기본적으로 위로 발사
            self.velocity = pygame.math.Vector2(0, -1) * 15

    def get_closest_enemy(self):
        """플레이어로부터 가장 가까운 적을 찾습니다."""
        closest_enemy = None
        min_dist = float('inf')
        
        for enemy in self.enemies:
            dist = pygame.math.Vector2(self.player.rect.center).distance_to(enemy.rect.center)
            if dist < min_dist:
                min_dist = dist
                closest_enemy = enemy
        return closest_enemy

    def update(self):
        """발사체 이동 및 화면 이탈 시 삭제"""
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y
        
        # 화면 밖으로 나가면 자동 삭제
        if not pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT).colliderect(self.rect):
            self.kill()
