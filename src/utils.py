# src/utils.py
import pygame

def load_image(path, scale=None):
    """
    이미지를 로드하고, 파일이 없을 경우 대체 이미지를 로드하며 로그를 남깁니다.
    scale: (width, height) 튜플로 크기 조절.
    """
    try:
        image = pygame.image.load(path).convert_alpha()
        if scale:
            image = pygame.transform.scale(image, scale)
        return image
    except (pygame.error, FileNotFoundError):
        print(f"파일 없음:({path}) - fileerror.png로 대체됨")
        try:
            error_path = "src/assets/images/fileerror.png"
            error_image = pygame.image.load(error_path).convert_alpha()
            if scale:
                error_image = pygame.transform.scale(error_image, scale)
            return error_image
        except (pygame.error, FileNotFoundError):
            # fileerror.png 마저도 없는 경우, 빨간색 사각형을 반환
            print(f"대체 이미지 'fileerror.png'도 찾을 수 없습니다!")
            if scale:
                fallback_surface = pygame.Surface(scale)
            else:
                fallback_surface = pygame.Surface((50, 50)) # 기본 크기
            fallback_surface.fill((255, 0, 0)) # 빨간색
            return fallback_surface
