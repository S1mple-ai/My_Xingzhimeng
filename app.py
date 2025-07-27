# ===== 导入必要的库 =====
# Flask: Python的轻量级Web框架，用于创建Web应用
# render_template: 用于渲染HTML模板
# request: 用于处理HTTP请求数据
# jsonify: 用于将Python数据转换为JSON格式返回给前端
from flask import Flask, render_template, request, redirect, url_for, jsonify
# Flask-SQLAlchemy: Flask的数据库扩展，简化数据库操作
from flask_sqlalchemy import SQLAlchemy
# 导入datetime用于处理时间
from datetime import datetime

# ===== 创建Flask应用实例 =====
app = Flask(__name__)

# ===== 数据库配置 =====
# 配置SQLite数据库文件路径，数据库文件名为 tasks.db
# sqlite:/// 表示使用SQLite数据库，三个斜杠后面是数据库文件名
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
# 关闭SQLAlchemy的事件系统，避免不必要的警告信息
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 创建数据库实例，用于操作数据库
db = SQLAlchemy(app)

# ===== 定义数据库模型 =====
# 定义分类数据模型
class Category(db.Model):
    # id字段：主键，自动递增的整数
    id = db.Column(db.Integer, primary_key=True)
    # name字段：分类名称，字符串类型，不能为空，唯一
    name = db.Column(db.String(50), nullable=False, unique=True)
    # color字段：分类颜色，用于前端显示
    color = db.Column(db.String(7), default='#007bff')
    # created_at字段：创建时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Task类继承自db.Model，代表数据库中的一张表
class Task(db.Model):
    # id字段：整数类型，主键，自动递增，用于唯一标识每个任务
    id = db.Column(db.Integer, primary_key=True)
    # content字段：字符串类型，最大长度200，不能为空，存储任务内容
    content = db.Column(db.String(200), nullable=False)
    # completed字段：布尔类型，默认值为False，表示任务是否完成
    completed = db.Column(db.Boolean, default=False)
    # priority字段：优先级，1=低，2=中，3=高
    priority = db.Column(db.Integer, default=2)
    # start_date字段：开始日期，可以为空
    start_date = db.Column(db.DateTime, nullable=True)
    # due_date字段：截止日期，可以为空
    due_date = db.Column(db.DateTime, nullable=True)
    # category_id字段：分类ID，外键关联到Category表
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    # order字段：排序顺序，用于拖拽排序
    order = db.Column(db.Integer, default=0)
    # created_at字段：创建时间，默认为当前时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # updated_at字段：更新时间
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 定义与Category的关系
    category = db.relationship('Category', backref=db.backref('tasks', lazy=True))

    # __repr__方法：定义对象的字符串表示，方便调试
    def __repr__(self):
        return f'<Task {self.id}: {self.content}>'
    
    # 将Task对象转换为字典格式，方便JSON序列化
    def to_dict(self):
        # 优先级映射：将数字转换为字符串
        priority_map = {1: 'low', 2: 'medium', 3: 'high'}
        priority_str = priority_map.get(self.priority, 'medium')
        
        return {
            'id': self.id,
            'content': self.content,
            'completed': self.completed,
            'priority': priority_str,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'order': self.order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# ===== 创建数据库表 =====
# 在应用上下文中创建所有数据库表
# 如果表已存在则不会重复创建
with app.app_context():
    db.create_all()

# ===== 路由定义 =====

# 主页路由：返回HTML模板
@app.route('/')
def index():
    return render_template('index.html')

# ===== 分类管理API =====

# 获取所有分类
@app.route('/api/categories', methods=['GET'])
def get_categories():
    try:
        categories = Category.query.all()
        return jsonify([category.to_dict() for category in categories])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 创建新分类
@app.route('/api/categories', methods=['POST'])
def create_category():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': '分类名称不能为空'}), 400
        
        # 检查分类名是否已存在
        existing = Category.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'error': '分类名称已存在'}), 400
        
        category = Category(
            name=data['name'],
            color=data.get('color', '#007bff')
        )
        db.session.add(category)
        db.session.commit()
        return jsonify(category.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 删除分类
@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    try:
        category = Category.query.get_or_404(category_id)
        # 将该分类下的任务的category_id设为None
        Task.query.filter_by(category_id=category_id).update({'category_id': None})
        db.session.delete(category)
        db.session.commit()
        return jsonify({'message': '分类删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===== 任务管理API =====

# 获取任务列表（支持搜索和过滤）
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    try:
        # 获取查询参数
        search = request.args.get('search', '').strip()
        category_id = request.args.get('category_id')
        completed = request.args.get('completed')
        priority = request.args.get('priority')
        
        # 构建查询
        query = Task.query
        
        # 搜索过滤
        if search:
            query = query.filter(Task.content.contains(search))
        
        # 分类过滤
        if category_id:
            if category_id == 'none':
                query = query.filter(Task.category_id.is_(None))
            else:
                query = query.filter(Task.category_id == int(category_id))
        
        # 完成状态过滤
        if completed is not None:
            query = query.filter(Task.completed == (completed.lower() == 'true'))
        
        # 优先级过滤
        if priority:
            priority_map = {'low': 1, 'medium': 2, 'high': 3}
            if priority in priority_map:
                priority_value = priority_map[priority]
            else:
                priority_value = int(priority)
            query = query.filter(Task.priority == priority_value)
        
        # 按order字段排序，然后按创建时间排序
        tasks = query.order_by(Task.order.asc(), Task.created_at.desc()).all()
        
        return jsonify([task.to_dict() for task in tasks])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 创建新任务
@app.route('/api/tasks', methods=['POST'])
def create_task():
    try:
        # 获取请求中的JSON数据
        data = request.get_json()
        
        # 验证数据：检查是否包含content字段且不为空
        if not data or 'content' not in data or not data['content'].strip():
            return jsonify({'error': '任务内容不能为空'}), 400
        
        # 处理开始日期
        start_date = None
        if data.get('start_date'):
            try:
                start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': '开始日期格式错误'}), 400
        
        # 处理截止日期
        due_date = None
        if data.get('due_date'):
            try:
                due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': '截止日期格式错误'}), 400
        
        # 验证日期逻辑：开始日期不能晚于截止日期
        if start_date and due_date and start_date > due_date:
            return jsonify({'error': '开始日期不能晚于截止日期'}), 400
        
        # 处理优先级转换
        priority_map = {'low': 1, 'medium': 2, 'high': 3}
        priority_value = data.get('priority', 'medium')
        if isinstance(priority_value, str):
            priority_value = priority_map.get(priority_value, 2)
        
        # 获取最大order值
        max_order = db.session.query(db.func.max(Task.order)).scalar() or 0
        
        # 创建新的Task对象
        new_task = Task(
            content=data['content'].strip(),
            priority=priority_value,
            start_date=start_date,
            due_date=due_date,
            category_id=data.get('category_id'),
            order=max_order + 1
        )
        
        # 添加到数据库会话并提交
        db.session.add(new_task)
        db.session.commit()
        
        # 返回新创建的任务信息，状态码201表示创建成功
        return jsonify(new_task.to_dict()), 201
    except Exception as e:
        # 如果出现错误，回滚事务
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 更新任务
@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        # 根据ID查找任务，如果不存在则返回404错误
        task = Task.query.get_or_404(task_id)
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求数据不能为空'}), 400
        
        # 更新任务字段
        if 'content' in data:
            if not data['content'].strip():
                return jsonify({'error': '任务内容不能为空'}), 400
            task.content = data['content'].strip()
        
        if 'completed' in data:
            task.completed = data['completed']
        
        if 'priority' in data:
            priority_map = {'low': 1, 'medium': 2, 'high': 3}
            priority_value = data['priority']
            if isinstance(priority_value, str):
                priority_value = priority_map.get(priority_value, 2)
            task.priority = priority_value
        
        if 'category_id' in data:
            task.category_id = data['category_id']
        
        if 'start_date' in data:
            if data['start_date']:
                try:
                    task.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({'error': '开始日期格式错误'}), 400
            else:
                task.start_date = None
        
        if 'due_date' in data:
            if data['due_date']:
                try:
                    task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({'error': '截止日期格式错误'}), 400
            else:
                task.due_date = None
        
        # 验证日期逻辑：开始日期不能晚于截止日期
        if task.start_date and task.due_date and task.start_date > task.due_date:
            return jsonify({'error': '开始日期不能晚于截止日期'}), 400
        
        # 提交更改到数据库
        db.session.commit()
        
        # 返回更新后的任务信息
        return jsonify(task.to_dict())
    except Exception as e:
        # 如果出现错误，回滚事务
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 批量更新任务
@app.route('/api/tasks/batch', methods=['PUT'])
def batch_update_tasks():
    try:
        data = request.get_json()
        if not data or 'task_ids' not in data:
            return jsonify({'error': '任务ID列表不能为空'}), 400
        
        task_ids = data['task_ids']
        updates = data.get('updates', {})
        
        # 批量更新
        query = Task.query.filter(Task.id.in_(task_ids))
        query.update(updates, synchronize_session=False)
        db.session.commit()
        
        return jsonify({'message': f'成功更新 {len(task_ids)} 个任务'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 更新任务排序
@app.route('/api/tasks/reorder', methods=['PUT'])
def reorder_tasks():
    try:
        data = request.get_json()
        if not data or 'task_orders' not in data:
            return jsonify({'error': '排序数据不能为空'}), 400
        
        # task_orders 格式: [{'id': 1, 'order': 0}, {'id': 2, 'order': 1}, ...]
        for item in data['task_orders']:
            task = Task.query.get(item['id'])
            if task:
                task.order = item['order']
        
        db.session.commit()
        return jsonify({'message': '排序更新成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 删除任务
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        # 根据ID查找任务
        task = Task.query.get_or_404(task_id)
        
        # 从数据库中删除任务
        db.session.delete(task)
        db.session.commit()
        
        # 返回删除成功的消息
        return jsonify({'message': '任务删除成功'})
    except Exception as e:
        # 如果出现错误，回滚事务
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 批量删除任务
@app.route('/api/tasks/batch', methods=['DELETE'])
def batch_delete_tasks():
    try:
        data = request.get_json()
        if not data or 'task_ids' not in data:
            return jsonify({'error': '任务ID列表不能为空'}), 400
        
        task_ids = data['task_ids']
        deleted_count = Task.query.filter(Task.id.in_(task_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({'message': f'成功删除 {deleted_count} 个任务'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ===== 统计API =====

# 获取任务统计信息
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        total_tasks = Task.query.count()
        completed_tasks = Task.query.filter_by(completed=True).count()
        pending_tasks = total_tasks - completed_tasks
        
        # 按优先级统计
        priority_stats = {}
        for priority in [1, 2, 3]:
            priority_stats[priority] = Task.query.filter_by(priority=priority).count()
        
        # 按分类统计
        category_stats = []
        categories = Category.query.all()
        for category in categories:
            count = Task.query.filter_by(category_id=category.id).count()
            category_stats.append({
                'category': category.to_dict(),
                'count': count
            })
        
        # 无分类任务数量
        no_category_count = Task.query.filter_by(category_id=None).count()
        if no_category_count > 0:
            category_stats.append({
                'category': {'id': None, 'name': '无分类', 'color': '#6c757d'},
                'count': no_category_count
            })
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return jsonify({
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': pending_tasks,
            'completion_rate': round(completion_rate, 1),
            'priority_stats': priority_stats,
            'category_stats': category_stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== 应用启动 =====
# 当直接运行此文件时（而不是被导入时），启动Flask开发服务器
if __name__ == '__main__':
    # debug=True 开启调试模式，代码修改后自动重启，显示详细错误信息
    app.run(debug=True)