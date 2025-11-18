import pygame
import random
from items import Coin
from config import COIN_COLLECTION_RADIUS
from utils import load_image

# 이 파일은 코인 시스템의 모든 로직(드랍, 수집, HUD 표시 등)을 관리합니다.

def handle_enemy_death_drops(enemy, all_sprites_group, all_coins_group):
    """적이 죽었을 때 코인 드랍을 처리합니다."""
    is_boss = "BOSS" in enemy.enemy_key.upper()
    
    if is_boss:
        # 보스는 50코인짜리 코인 10개를 드랍
        for _ in range(10):
            coin = Coin(enemy.rect.center)
            coin.value = 50
            all_sprites_group.add(coin)
            all_coins_group.add(coin)
    else:
        # 일반 몬스터는 50% 확률로 10코인짜리 코인 1개 드랍
        if random.random() < 0.5:
            coin = Coin(enemy.rect.center)
            coin.value = 10
            all_sprites_group.add(coin)
            all_coins_group.add(coin)

def update_coin_collection(player, all_coins_group):
    """플레이어와 코인 그룹 간의 충돌을 감지하고 코인을 수집합니다."""
    # 플레이어의 충돌 범위를 확장하여 코인 수집 거리를 늘립니다.
    enlarged_player_rect = player.rect.inflate(COIN_COLLECTION_RADIUS * 2, COIN_COLLECTION_RADIUS * 2)
    
    collected_coins = pygame.sprite.spritecollide(player, all_coins_group, True, collided=lambda sprite, other: enlarged_player_rect.colliderect(other.rect))
    for coin in collected_coins:
        player.coins += coin.value

def draw_coin_hud(surface, player):
    """화면에 코인 HUD를 그립니다."""
    coin_icon = load_image("src/assets/images/coin.png", scale=(30, 30))
    surface.blit(coin_icon, (10, 110)) # 레벨 아래로 위치 조정
    
    # 폰트 로드 (main.py와 별개로 로드 필요)
    try:
        font_path = "src/assets/fonts/Pretendard-Light.otf"
        desc_font = pygame.font.Font(font_path, 36)
    except FileNotFoundError:
        desc_font = pygame.font.Font(None, 40)
        
    coin_text = f"{player.coins}"
    
    text_obj = desc_font.render(coin_text, True, (255, 223, 0))
    text_rect = text_obj.get_rect(topleft=(50, 112)) # 아이콘 옆
    surface.blit(text_obj, text_rect)

