from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import random
import json

app = Flask(__name__)
CORS(app)

class MatchGame:
    def __init__(self, rows=8, cols=8):
        self.rows = rows
        self.cols = cols
        self.colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange']
        self.board = []
        self.score = 0
        self.moves = 0
        self.init_board()
    
    def init_board(self):
        """初始化游戏板，确保没有初始匹配"""
        self.board = []
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                # 避免创建初始匹配
                available_colors = self.colors.copy()
                
                # 检查左边两个
                if j >= 2 and row[j-1] == row[j-2]:
                    if row[j-1] in available_colors:
                        available_colors.remove(row[j-1])
                
                # 检查上面两个
                if i >= 2 and self.board[i-1][j] == self.board[i-2][j]:
                    if self.board[i-1][j] in available_colors:
                        available_colors.remove(self.board[i-1][j])
                
                color = random.choice(available_colors)
                row.append(color)
            self.board.append(row)
    
    def find_matches(self):
        """找到所有匹配的组合"""
        matches = set()
        
        # 检查水平匹配
        for i in range(self.rows):
            j = 0
            while j < self.cols:
                current_color = self.board[i][j]
                if current_color is None:
                    j += 1
                    continue
                    
                count = 1
                start_j = j
                
                # 计算连续相同颜色的数量
                while j + 1 < self.cols and self.board[i][j + 1] == current_color:
                    count += 1
                    j += 1
                
                # 如果连续3个或以上，添加到匹配集合
                if count >= 3:
                    for k in range(start_j, start_j + count):
                        matches.add((i, k))
                
                j += 1
        
        # 检查垂直匹配
        for j in range(self.cols):
            i = 0
            while i < self.rows:
                current_color = self.board[i][j]
                if current_color is None:
                    i += 1
                    continue
                    
                count = 1
                start_i = i
                
                # 计算连续相同颜色的数量
                while i + 1 < self.rows and self.board[i + 1][j] == current_color:
                    count += 1
                    i += 1
                
                # 如果连续3个或以上，添加到匹配集合
                if count >= 3:
                    for k in range(start_i, start_i + count):
                        matches.add((k, j))
                
                i += 1
        
        return matches
    
    def remove_matches(self, matches):
        """移除匹配的方块"""
        for row, col in matches:
            self.board[row][col] = None
        self.score += len(matches) * 10
    
    def drop_pieces(self):
        """让方块下落"""
        for j in range(self.cols):
            # 收集非空方块
            column = []
            for i in range(self.rows):
                if self.board[i][j] is not None:
                    column.append(self.board[i][j])
            
            # 填充新的随机方块
            while len(column) < self.rows:
                column.insert(0, random.choice(self.colors))
            
            # 更新列
            for i in range(self.rows):
                self.board[i][j] = column[i]
    
    def is_valid_swap(self, row1, col1, row2, col2):
        """检查交换是否有效（相邻且会产生匹配）"""
        # 检查是否相邻
        if abs(row1 - row2) + abs(col1 - col2) != 1:
            return False
        
        # 临时交换
        self.board[row1][col1], self.board[row2][col2] = self.board[row2][col2], self.board[row1][col1]
        
        # 检查是否产生匹配
        matches = self.find_matches()
        has_matches = len(matches) > 0
        
        # 恢复交换
        self.board[row1][col1], self.board[row2][col2] = self.board[row2][col2], self.board[row1][col1]
        
        return has_matches
    
    def make_move(self, row1, col1, row2, col2):
        """执行移动"""
        if not self.is_valid_swap(row1, col1, row2, col2):
            return False, [], None, []
        
        # 执行交换
        self.board[row1][col1], self.board[row2][col2] = self.board[row2][col2], self.board[row1][col1]
        self.moves += 1
        
        # 保存交换后的初始状态（用于前端显示）
        board_after_swap = [row[:] for row in self.board]
        
        # 收集所有匹配信息（按轮次分组）
        all_matches = []
        chain_steps = []  # 记录每一轮连锁的详细信息
        
        # 处理连锁反应
        while True:
            matches = self.find_matches()
            if not matches:
                break
            
            # 记录这一轮的匹配信息
            matches_list = list(matches)
            all_matches.extend(matches_list)
            
            # 保存这一轮的状态（消除前）
            board_before_remove = [row[:] for row in self.board]
            
            # 消除匹配的方块
            self.remove_matches(matches)
            
            # 保存这一轮的状态（消除后，下落前）
            board_after_remove = [row[:] for row in self.board]
            
            # 方块下落
            self.drop_pieces()
            
            # 保存这一轮的状态（下落后）
            board_after_drop = [row[:] for row in self.board]
            
            # 记录这一轮的详细信息
            chain_steps.append({
                'matches': matches_list,
                'board_before': board_before_remove,
                'board_after_drop': board_after_drop
            })
        
        return True, all_matches, board_after_swap, chain_steps
    
    def get_state(self):
        """获取游戏状态"""
        return {
            'board': self.board,
            'score': self.score,
            'moves': self.moves
        }

# 全局游戏实例
game = MatchGame()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/new_game', methods=['POST'])
def new_game():
    global game
    game = MatchGame()
    return jsonify(game.get_state())

@app.route('/api/move', methods=['POST'])
def make_move():
    data = request.json
    row1, col1 = data['from']
    row2, col2 = data['to']
    
    success, matches, board_after_swap, chain_steps = game.make_move(row1, col1, row2, col2)
    
    return jsonify({
        'success': success,
        'matches': matches,
        'board_after_swap': board_after_swap,
        'chain_steps': chain_steps,  # 新增：每一轮连锁的详细信息
        'state': game.get_state()
    })

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(game.get_state())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8081)
