# -*- coding: utf-8 -*-

import pygame

# --- 화면 설정 ---
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60
SCREEN_RECT = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

# --- 색상 ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
LIGHT_GRAY = (170, 170, 170)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)

# --- 게임 플레이 설정 ---
COIN_COLLECTION_RADIUS = 50 # 코인 수집 반경 (픽셀)

# --- 플레이어 레벨업 스탯 증가 설정 ---
PLAYER_HP_PER_LEVEL = 50
PLAYER_ATTACK_POWER_PER_LEVEL = 10
PLAYER_DEFENSE_PER_LEVEL = 1
PLAYER_MOVE_SPEED_PER_LEVEL_MULTIPLIER = 1.01 # 1% 증가

# --- 캐릭터 정보 ---
# 기획서에 명시된 스탯을 기반으로 작성
# key: 캐릭터 영문명 (코드 내에서 사용할 이름)
# value: 상세 정보 딕셔너리
CHARACTERS = {
    "swordsman": {
        "name": "검사",
        "hp": 3000,
        "attack_power": 180,
        "attack_speed": 0.5,
        "move_speed": 10,
        "description": "스플래쉬 데미지를 입힙니다.",
        "splash_radius": 75, # 스플래쉬 데미지 반경
        "skill_text": "스킬: 대쉬하며 범위 공격",
        "skill_damage": 300,
        "skill_cooldown": 5000,
    },
    "archer": {
        "name": "궁수",
        "hp": 1500,
        "attack_power": 400,
        "attack_speed": 0.6,
        "move_speed": 15,
        "description": "원거리 단일 데미지를 입힙니다.",
        "splash_radius": 0,
        "skill_text": "스킬: 거대한 화살로 범위 공격",
        "skill_damage": 500,
        "skill_cooldown": 7000,
    },
    "viking": {
        "name": "바이킹",
        "hp": 2000,
        "attack_power": 400,
        "attack_speed": 0.4,
        "move_speed": 20,
        "description": "3타마다 범위 공격을 합니다.",
        "splash_radius": 0, # 3타 스킬은 별도 구현
        "skill_text": "스킬: 5초간 광폭화",
        "skill_duration": 5000,
        "skill_cooldown": 10000,
        "skill_stats": {"move_speed": 40, "attack_power": 600, "attack_speed": 0.2},
    },
    "wizard": {
        "name": "마법사",
        "hp": 1300,
        "attack_power": 500,
        "attack_speed": 1.0,
        "move_speed": 10,
        "description": "원거리 스플래쉬 데미지를 입힙니다.",
        "splash_radius": 90, # 스플래쉬 데미지 반경
        "skill_text": "스킬: 5초간 마력 증폭",
        "skill_duration": 5000,
        "skill_cooldown": 9000,
        "skill_stats": {"attack_power": 700},
    },
    "assassin": {
        "name": "암살자",
        "hp": 1000,
        "attack_power": 500,
        "attack_speed": 0.2,
        "move_speed": 25,
        "description": "빠른 속도로 단일 데미지를 입힙니다.",
        "splash_radius": 0,
        "skill_text": "스킬: 전방위 표창 발사",
        "skill_damage": 500,
        "skill_cooldown": 10000,
    }
}

# --- 적 정보 ---
# 구상안에 명시된 '불 스테이지'의 적 정보
# 적의 이동 속도는 밸런스를 위해 플레이어보다 느리게 초기 설정 (예: 3)
ENEMIES = {
    # 불 스테이지
    "black_demon": {
        "name": "검은 악마",
        "hp": 200,
        "attack_power": 40,
        "move_speed": 3,
        "exp": 100
    },
    "axe_demon": {
        "name": "도끼든 악마",
        "hp": 500,
        "attack_power": 75,
        "move_speed": 3,
        "exp": 200
    },
    "sword_demon": {
        "name": "칼든 악마",
        "hp": 500,
        "attack_power": 100,
        "move_speed": 3,
        "exp": 300
    },
    # 얼음 스테이지
    "white_cutie": {
        "name": "흰색 귀요미",
        "hp": 200,
        "attack_power": 75,
        "move_speed": 3,
        "exp": 100
    },
    "blue_slime": {
        "name": "파란 슬라임",
        "hp": 700,
        "attack_power": 40,
        "move_speed": 3, # 원안: 5
        "exp": 200
    },
    "ice_giant": {
        "name": "얼음거인",
        "hp": 1200,
        "attack_power": 50,
        "move_speed": 3,
        "exp": 300
    },
    # 독 스테이지
    "snake": {
        "name": "뱀",
        "hp": 200,
        "attack_power": 40,
        "move_speed": 3,
        "exp": 100
    },
    "spear_snake": {
        "name": "창든 뱀",
        "hp": 300,
        "attack_power": 75,
        "move_speed": 3,
        "exp": 200
    },
    "eye_monster": {
        "name": "눈알괴물",
        "hp": 800,
        "attack_power": 100,
        "move_speed": 3,
        "exp": 300
    },
    # 공허 스테이지
    "skeleton": {
        "name": "해골",
        "hp": 200,
        "attack_power": 50,
        "move_speed": 3,
        "exp": 100
    },
    "armored_skeleton": {
        "name": "갑옷해골",
        "hp": 400,
        "attack_power": 100,
        "move_speed": 3,
        "exp": 200
    },
    "ghost": {
        "name": "귀신",
        "hp": 700,
        "attack_power": 150,
        "move_speed": 3, # 원안: 13
        "exp": 300
    },
    # --- 보스 ---
    "fire_boss": {
        "name": "화염 군주",
        "hp": 10000,
        "attack_power": 300,
        "move_speed": 2,
        "exp": 0 # 보스는 경험치 대신 즉시 레벨업
    },
    "ice_boss": {
        "name": "빙하의 주인",
        "hp": 12000,
        "attack_power": 375,
        "move_speed": 2,
        "exp": 0
    },
    "poison_boss": {
        "name": "독의 화신",
        "hp": 14000,
        "attack_power": 450,
        "move_speed": 2,
        "exp": 0
    },
    "void_boss": {
        "name": "공허의 그림자",
        "hp": 16000,
        "attack_power": 525,
        "move_speed": 2,
        "exp": 0
    },
    "fileerror": {
        "name": "파일 오류",
        "hp": 1,
        "attack_power": 0,
        "move_speed": 0,
        "exp": 0
    }
}

# --- 증강 정보 ---
AUGMENTS = {
    "hp_boost": {
        "name": "체력 증강",
        "description": "최대 체력 20% 증가",
        "effect": {"max_hp_multiplier": 1.2}
    },
    "attack_boost": {
        "name": "공격력 증강",
        "description": "공격력 15% 증가",
        "effect": {"attack_power_multiplier": 1.15}
    },
    "speed_boost": {
        "name": "이동 속도 증강",
        "description": "이동 속도 20% 증가",
        "effect": {"move_speed_multiplier": 1.2}
    },
    "skill_haste": {
        "name": "스킬 가속",
        "description": "스킬 쿨다운 10% 감소",
        "effect": {"skill_cooldown_multiplier": 0.9}
    },
    "splash_increase": {
        "name": "스플래쉬 범위 증가",
        "description": "스플래쉬 범위 25% 증가",
        "effect": {"splash_radius_multiplier": 1.25}
    }
}

# --- 스테이지 정보 ---
STAGES = [
    {
        "name": "불 스테이지",
        "enemies": ["black_demon", "axe_demon", "sword_demon"],
        "boss": "fire_boss" # 보스 키 (추후 정의)
    },
    {
        "name": "얼음 스테이지",
        "enemies": ["white_cutie", "blue_slime", "ice_giant"],
        "boss": "ice_boss"
    },
    {
        "name": "독 스테이지",
        "enemies": ["snake", "spear_snake", "eye_monster"],
        "boss": "poison_boss"
    },
    {
        "name": "공허 스테이지",
        "enemies": ["skeleton", "armored_skeleton", "ghost"],
        "boss": "void_boss"
    }
]

# --- 상점 아이템 정보 ---
SHOP_ITEMS = {
    "health_potion": {
        "name": "체력 포션",
        "type": "consumable",
        "stat": "hp",
        "icon": "health_potion.png",
        "value_range": (100, 500), # 회복량 범위
        "price_multiplier": 0.5 # 가치 1당 가격
    },
    "xp_potion": {
        "name": "경험치 포션",
        "type": "consumable",
        "stat": "exp",
        "icon": "xp_potion.png",
        "value_range": (200, 1000), # 경험치 획득량 범위
        "price_multiplier": 0.3
    },
    "attack_boost_item": {
        "name": "공격력 증폭기",
        "type": "temporary_stat_boost",
        "stat": "attack_power",
        "duration": 10, # 10레벨 동안 지속
        "icon": "attack_boost_icon.png",
        "value_range": (10, 50), # 공격력 증가량 범위
        "price_multiplier": 10
    },
    "defense_boost_item": {
        "name": "방어력 증폭기",
        "type": "temporary_stat_boost",
        "stat": "defense", # 플레이어에게 defense 속성 추가 필요
        "duration": 10,
        "icon": "defense_boost_icon.png",
        "value_range": (5, 25), # 방어력 증가량 범위
        "price_multiplier": 12
    },
    "speed_boost_item": {
        "name": "신속의 비약",
        "type": "temporary_stat_boost",
        "stat": "move_speed",
        "duration": 10,
        "icon": "speed_boost_icon.png",
        "value_range": (1, 5), # 이동속도 증가량 범위
        "price_multiplier": 50
    }
}
