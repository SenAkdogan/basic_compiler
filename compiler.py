import sys

# --- 1. TOKEN TİPLERİ ---
INTEGER = 'INTEGER'
STRING  = 'STRING'
ID      = 'ID'
ASSIGN  = 'ASSIGN'
PLUS    = 'PLUS'
MINUS   = 'MINUS'
MUL     = 'MUL'
DIV     = 'DIV'
LPAREN  = 'LPAREN'
RPAREN  = 'RPAREN'
EQ      = 'EQ'  # ==
NEQ     = 'NEQ' # !=
LT      = 'LT'  # <
GT      = 'GT'  # >
# YENİ: Karar Yapıları
IF      = 'IF'
THEN    = 'THEN'
ELSE    = 'ELSE'
EOF     = 'EOF'

class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return f'Token({self.type}, {repr(self.value)})'

# --- 2. LEXER ---
class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos]
        # YENİ: Ayrılmış Kelimeler (Bunlar değişken ismi olamaz)
        self.RESERVED_KEYWORDS = {
            'if': Token(IF, 'if'),
            'then': Token(THEN, 'then'),
            'else': Token(ELSE, 'else')
        }

    def error(self):
        raise Exception(f"Hata: Geçersiz karakter '{self.current_char}'")

    def advance(self):
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]

    def peek(self):
        peek_pos = self.pos + 1
        if peek_pos > len(self.text) - 1:
            return None
        return self.text[peek_pos]

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def string(self):
        result = ''
        self.advance()
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        self.advance()
        return result

    def _id(self):
        """Değişken isimlerini VE anahtar kelimeleri (if, else) okur"""
        result = ''
        while self.current_char is not None and self.current_char.isalnum():
            result += self.current_char
            self.advance()
        
        # YENİ: Eğer okuduğumuz kelime 'if', 'then' veya 'else' ise özel token döndür
        # Değilse normal değişken (ID) döndür
        token = self.RESERVED_KEYWORDS.get(result, Token(ID, result))
        return token

    def get_all_tokens(self):
        tokens = []
        
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                tokens.append(Token(INTEGER, self.integer()))
                continue
            
            if self.current_char == '"':
                tokens.append(Token(STRING, self.string()))
                continue

            if self.current_char.isalpha():
                # Artık _id fonksiyonu hem değişkenleri hem if/else'i hallediyor
                tokens.append(self._id())
                continue

            if self.current_char == '=':
                if self.peek() == '=': 
                    self.advance()
                    self.advance()
                    tokens.append(Token(EQ, '=='))
                else:
                    self.advance()
                    tokens.append(Token(ASSIGN, '='))
                continue

            if self.current_char == '!':
                if self.peek() == '=':
                    self.advance()
                    self.advance()
                    tokens.append(Token(NEQ, '!='))
                    continue
                else:
                    self.error()

            if self.current_char == '<':
                self.advance()
                tokens.append(Token(LT, '<'))
                continue

            if self.current_char == '>':
                self.advance()
                tokens.append(Token(GT, '>'))
                continue

            if self.current_char == '+':
                self.advance()
                tokens.append(Token(PLUS, '+'))
                continue

            if self.current_char == '-':
                self.advance()
                tokens.append(Token(MINUS, '-'))
                continue

            if self.current_char == '*':
                self.advance()
                tokens.append(Token(MUL, '*'))
                continue

            if self.current_char == '/':
                self.advance()
                tokens.append(Token(DIV, '/'))
                continue

            if self.current_char == '(':
                self.advance()
                tokens.append(Token(LPAREN, '('))
                continue

            if self.current_char == ')':
                self.advance()
                tokens.append(Token(RPAREN, ')'))
                continue

            self.error()

        tokens.append(Token(EOF, None))
        return tokens

# --- 3. INTERPRETER ---
class Interpreter:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos]
        self.GLOBAL_SCOPE = {} 

    def error(self):
        raise Exception('Hata: Sözdizimi hatası!')

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.pos += 1
            if self.pos < len(self.tokens):
                self.current_token = self.tokens[self.pos]
        else:
            self.error()

    def peek(self):
        peek_pos = self.pos + 1
        if peek_pos < len(self.tokens):
            return self.tokens[peek_pos]
        return None

    def factor(self):
        token = self.current_token
        if token.type == INTEGER:
            self.eat(INTEGER)
            return token.value
        elif token.type == STRING:
            self.eat(STRING)
            return token.value
        elif token.type == ID:
            var_name = token.value
            self.eat(ID)
            if var_name in self.GLOBAL_SCOPE:
                return self.GLOBAL_SCOPE[var_name]
            else:
                raise Exception(f"Hata: '{var_name}' tanımlı değil!")
        elif token.type == LPAREN:
            self.eat(LPAREN)
            result = self.comp_expr() 
            self.eat(RPAREN)
            return result
        self.error()

    def term(self):
        result = self.factor()
        while self.current_token.type in (MUL, DIV):
            token = self.current_token
            if token.type == MUL:
                self.eat(MUL)
                result = result * self.factor()
            elif token.type == DIV:
                self.eat(DIV)
                result = int(result / self.factor())
        return result

    def expr(self):
        result = self.term()
        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
                result = result + self.term()
            elif token.type == MINUS:
                self.eat(MINUS)
                result = result - self.term()
        return result

    def comp_expr(self):
        result = self.expr()
        if self.current_token.type in (EQ, NEQ, LT, GT):
            token = self.current_token
            if token.type == EQ:
                self.eat(EQ)
                result = (result == self.expr()) 
            elif token.type == NEQ:
                self.eat(NEQ)
                result = (result != self.expr())
            elif token.type == LT:
                self.eat(LT)
                result = (result < self.expr())
            elif token.type == GT:
                self.eat(GT)
                result = (result > self.expr())
        return result

    def statement(self):
        # 1. DURUM: Değişken Atama (x = ...)
        if self.current_token.type == ID and self.peek().type == ASSIGN:
            var_name = self.current_token.value
            self.eat(ID)
            self.eat(ASSIGN)
            value = self.statement() # Recursive çağrı
            self.GLOBAL_SCOPE[var_name] = value
            return value
        
        # 2. DURUM: IF STATEMENT (if ... then ... else ...)
        elif self.current_token.type == IF:
            self.eat(IF)
            # Şartı kontrol et
            condition = self.comp_expr()
            
            self.eat(THEN)
            # Eğer şart doğruysa burayı çalıştır
            true_result = self.statement()
            
            # Else kısmı (Opsiyonel yapılabilir ama biz zorunlu tutalım şimdilik)
            if self.current_token.type == ELSE:
                self.eat(ELSE)
                false_result = self.statement()
                
                if condition:
                    return true_result
                else:
                    return false_result
            
            # Else yoksa ve şart doğruysa sonucu dön
            if condition:
                return true_result
            return None

        # 3. DURUM: Normal İşlem
        else:
            return self.comp_expr()

# --- TEST ---
def main():
    print("Çıkmak için CTRL+C veya boş entere basın.")
    global_scope = {} 

    while True:
        try:
            # Versiyon kontrolü için V9 yazalım
            text = input('calc V9 > ')
        except EOFError:
            break
        if not text:
            continue

        try:
            lexer = Lexer(text)
            tokens = lexer.get_all_tokens()
            interpreter = Interpreter(tokens)
            interpreter.GLOBAL_SCOPE = global_scope
            
            result = interpreter.statement()
            global_scope = interpreter.GLOBAL_SCOPE

            if result is not None:
                if isinstance(result, str):
                    print(f"'{result}'")
                else:
                    print(result)
                    
        except Exception as e:
            print(e)

if __name__ == '__main__':
    main()