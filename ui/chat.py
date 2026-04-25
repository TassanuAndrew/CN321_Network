"""
Chat UI
"""
import pygame
import time

class ChatBox:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.messages = []
        self.input_text = ""
        self.active = False
        self.visible = True  # Toggle visibility
        self.max_messages = 6
        self.font = pygame.font.Font(None, 18)
    
    def add_message(self, name, text):
        self.messages.append({"name": name, "text": text})
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.active:
                    # Already typing - send message
                    if self.input_text.strip():
                        message = self.input_text
                        self.input_text = ""
                        self.active = False  # Close after sending
                        return message
                    else:
                        # Empty message - just close
                        self.active = False
                else:
                    # Not typing - open chat box
                    self.active = True
            elif event.key == pygame.K_ESCAPE:
                self.input_text = ""
                self.active = False
            elif event.key == pygame.K_TAB:
                # Tab to toggle visibility
                self.visible = not self.visible
                self.active = False
                self.input_text = ""
            elif self.active:
                # Only accept typing when active
                if event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif len(self.input_text) < 40 and event.unicode.isprintable():
                    self.input_text += event.unicode
        return None

    def is_mouse_over(self, mouse_pos):
        """Check if mouse is over chat box"""
        mx, my = mouse_pos
        return (self.x <= mx <= self.x + self.width and 
                self.y <= my <= self.y + self.height)
    
    def draw(self, screen):
        if not self.visible:
            # Show toggle hint when hidden
            hint = self.font.render("TAB: Show Chat", True, (150, 150, 150))
            
            return screen.blit(hint, (10, pygame.display.get_surface().get_height() - 25))
        
        # Background
        bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(bg, (0, 0, 0, 150), (0, 0, self.width, self.height), border_radius=8)
        screen.blit(bg, (self.x, self.y))
        
        # Title with toggle hint
        # Title
        title = self.font.render("Chat (TAB: Hide)", True, (200, 200, 255))
        screen.blit(title, (self.x + 5, self.y + 3))
        
        # Messages
        msg_y = self.y + 22
        for msg in self.messages[-self.max_messages:]:
            name_text = self.font.render(f"{msg['name']}:", True, (255, 200, 100))
            screen.blit(name_text, (self.x + 5, msg_y))
            msg_text = self.font.render(msg['text'], True, (255, 255, 255))
            screen.blit(msg_text, (self.x + 70, msg_y))
            msg_y += 18
        
        # Input
        input_y = self.y + self.height - 22
        input_color = (40, 40, 60) if self.active else (20, 20, 40)
        pygame.draw.rect(screen, input_color, (self.x + 3, input_y, self.width - 6, 20), border_radius=4)
        
        if self.active:
            pygame.draw.rect(screen, (100, 150, 255), (self.x + 3, input_y, self.width - 6, 20), 2, border_radius=4)
        
        display_text = self.input_text
        if self.active and int(time.time() * 2) % 2 == 0:
            display_text += "|"
        
        input_surface = self.font.render(display_text, True, (255, 255, 255))
        screen.blit(input_surface, (self.x + 8, input_y + 4))
        
        if not self.input_text and not self.active:
            placeholder = self.font.render("Type to chat...", True, (100, 100, 100))
            screen.blit(placeholder, (self.x + 8, input_y + 4))
