// ===== 全局变量和页面元素引用 =====
// 获取页面中的各种元素，用于后续操作
const taskInput = document.getElementById('task-input');
const addButton = document.getElementById('add-button');
const taskList = document.getElementById('task-list');
const emptyState = document.getElementById('empty-state');

// 新增功能的元素引用
const categorySelect = document.getElementById('category-select');
const prioritySelect = document.getElementById('priority-select');
const startDateInput = document.getElementById('start-date');
const dueDateInput = document.getElementById('due-date');
const searchInput = document.getElementById('search-input');
const filterCompleted = document.getElementById('filter-completed');
const filterCategory = document.getElementById('filter-category');
const filterPriority = document.getElementById('filter-priority');
const selectAllCheckbox = document.getElementById('select-all');
const batchCompleteBtn = document.getElementById('batch-complete');
const batchDeleteBtn = document.getElementById('batch-delete');

// 分类管理元素
const categoryInput = document.getElementById('category-input');
const addCategoryBtn = document.getElementById('add-category');
const categoryList = document.getElementById('category-list');

// 统计面板元素
const totalTasksSpan = document.getElementById('total-tasks');
const completedTasksSpan = document.getElementById('completed-tasks');
const pendingTasksSpan = document.getElementById('pending-tasks');
const completionRateSpan = document.getElementById('completion-rate');

// 全局状态变量
let allTasks = [];          // 存储所有任务数据
let allCategories = [];     // 存储所有分类数据
let selectedTasks = [];     // 存储当前选中的任务ID
let sortable = null;        // 拖拽排序实例

// ===== 页面初始化 =====
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 应用初始化函数
function initializeApp() {
    // 加载数据
    fetchCategories();
    fetchTasks();
    loadStatistics();
    
    // 初始化拖拽排序
    initializeSortable();
    
    // 绑定事件监听器
    bindEventListeners();
}

// ===== 事件监听器绑定 =====
function bindEventListeners() {
    // 基础功能事件
    addButton.addEventListener('click', addTask);
    taskInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') addTask();
    });
    
    // 搜索和过滤事件
    searchInput.addEventListener('input', applyFilters);
    filterCompleted.addEventListener('change', applyFilters);
    filterCategory.addEventListener('change', applyFilters);
    filterPriority.addEventListener('change', applyFilters);
    
    // 批量操作事件
    selectAllCheckbox.addEventListener('change', toggleSelectAll);
    batchCompleteBtn.addEventListener('click', batchComplete);
    batchDeleteBtn.addEventListener('click', batchDelete);
    
    // 分类管理事件
    addCategoryBtn.addEventListener('click', addCategory);
    categoryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') addCategory();
    });
}

// ===== 分类管理功能 =====
// 获取所有分类
function fetchCategories() {
    fetch('/api/categories')
        .then(response => response.json())
        .then(categories => {
            allCategories = categories;
            updateCategorySelects();
            renderCategories();
        })
        .catch(error => {
            console.error('Error fetching categories:', error);
        });
}

// 添加新分类
function addCategory() {
    const name = categoryInput.value.trim();
    if (!name) {
        alert('请输入分类名称');
        return;
    }
    
    fetch('/api/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name })
    })
    .then(response => response.json())
    .then(newCategory => {
        categoryInput.value = '';
        allCategories.push(newCategory);
        updateCategorySelects();
        renderCategories();
    })
    .catch(error => {
        console.error('Error adding category:', error);
        alert('添加分类失败');
    });
}

// 删除分类
function deleteCategory(categoryId) {
    if (!confirm('确定要删除这个分类吗？删除后该分类下的任务将变为无分类。')) {
        return;
    }
    
    fetch(`/api/categories/${categoryId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (response.ok) {
            allCategories = allCategories.filter(cat => cat.id !== categoryId);
            updateCategorySelects();
            renderCategories();
            fetchTasks(); // 重新加载任务以更新显示
        }
    })
    .catch(error => {
        console.error('Error deleting category:', error);
        alert('删除分类失败');
    });
}

// 渲染分类列表
function renderCategories() {
    categoryList.innerHTML = '';
    allCategories.forEach(category => {
        const categoryItem = document.createElement('div');
        categoryItem.className = 'category-item';
        categoryItem.innerHTML = `
            <span class="category-name">${category.name}</span>
            <button class="delete-category-btn" onclick="deleteCategory(${category.id})">
                <i class="fas fa-trash"></i>
            </button>
        `;
        categoryList.appendChild(categoryItem);
    });
}

// 更新分类选择框
function updateCategorySelects() {
    // 更新添加任务时的分类选择
    categorySelect.innerHTML = '<option value="">无分类</option>';
    // 更新过滤器的分类选择
    filterCategory.innerHTML = '<option value="">所有分类</option>';
    
    allCategories.forEach(category => {
        const option1 = document.createElement('option');
        option1.value = category.id;
        option1.textContent = category.name;
        categorySelect.appendChild(option1);
        
        const option2 = document.createElement('option');
        option2.value = category.id;
        option2.textContent = category.name;
        filterCategory.appendChild(option2);
    });
}

// ===== 任务管理功能 =====
// 获取任务（支持搜索和过滤）
function fetchTasks() {
    const params = new URLSearchParams();
    
    // 添加搜索参数
    const search = searchInput.value.trim();
    if (search) params.append('search', search);
    
    // 添加过滤参数
    const completed = filterCompleted.value;
    if (completed !== '') params.append('completed', completed);
    
    const categoryId = filterCategory.value;
    if (categoryId) params.append('category_id', categoryId);
    
    const priority = filterPriority.value;
    if (priority) params.append('priority', priority);
    
    const url = `/api/tasks${params.toString() ? '?' + params.toString() : ''}`;
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(tasks => {
            // 确保tasks是数组
            if (Array.isArray(tasks)) {
                allTasks = tasks;
                renderTasks();
                updateBatchButtons();
            } else {
                console.error('API返回的不是数组:', tasks);
                allTasks = [];
                renderTasks();
            }
        })
        .catch(error => {
            console.error('Error fetching tasks:', error);
            allTasks = [];
            renderTasks();
            alert('获取任务列表失败');
        });
}

// 添加新任务
function addTask() {
    const content = taskInput.value.trim();
    if (!content) {
        alert('请输入任务内容');
        return;
    }
    
    // 获取日期值
    const startDate = startDateInput.value || null;
    const dueDate = dueDateInput.value || null;
    
    // 验证日期逻辑
    if (startDate && dueDate && new Date(startDate) > new Date(dueDate)) {
        alert('开始日期不能晚于截止日期');
        return;
    }
    
    const taskData = {
        content: content,
        priority: prioritySelect.value || 'medium',
        start_date: startDate,
        due_date: dueDate,
        category_id: categorySelect.value || null
    };
    
    fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
    })
    .then(response => response.json())
    .then(newTask => {
        // 清空输入
        taskInput.value = '';
        startDateInput.value = '';
        dueDateInput.value = '';
        prioritySelect.value = 'medium';
        categorySelect.value = '';
        
        // 重新加载任务和统计
        fetchTasks();
        loadStatistics();
    })
    .catch(error => {
        console.error('Error adding task:', error);
        alert('添加任务失败');
    });
}

// 渲染任务列表
function renderTasks() {
    taskList.innerHTML = '';
    selectedTasks = [];
    
    if (allTasks.length === 0) {
        showEmptyState();
        return;
    }
    
    hideEmptyState();
    allTasks.forEach(task => renderTask(task));
    
    // 重新初始化拖拽排序
    if (sortable) {
        sortable.destroy();
    }
    initializeSortable();
}

// 渲染单个任务
function renderTask(task) {
    const taskItem = document.createElement('li');
    taskItem.className = 'task-item';
    taskItem.dataset.id = task.id;
    
    // 获取分类名称
    const categoryName = task.category ? task.category.name : '';
    
    // 格式化日期
    const startDate = task.start_date ? new Date(task.start_date).toLocaleDateString() : '';
    const dueDate = task.due_date ? new Date(task.due_date).toLocaleDateString() : '';
    
    // 优先级显示
    const priorityText = {
        'high': '高',
        'medium': '中', 
        'low': '低'
    }[task.priority] || '中';
    
    // 优先级颜色类
    const priorityClass = `priority-${task.priority}`;
    
    taskItem.innerHTML = `
        <div class="task-select">
            <input type="checkbox" class="task-checkbox" onchange="toggleTaskSelection(${task.id})">
        </div>
        <div class="task-complete">
            <input type="checkbox" class="complete-checkbox" ${task.completed ? 'checked' : ''} 
                   onchange="toggleTaskCompletion(${task.id})">
        </div>
        <div class="task-content-wrapper">
            <div class="task-content ${task.completed ? 'completed' : ''}" 
                 ondblclick="editTask(${task.id})">${task.content}</div>
            <div class="task-meta">
                ${categoryName ? `<span class="task-category"><i class="fas fa-tag"></i> ${categoryName}</span>` : ''}
                <span class="task-priority ${priorityClass}"><i class="fas fa-flag"></i> ${priorityText}</span>
                ${startDate ? `<span class="task-start-date"><i class="fas fa-play"></i> 开始: ${startDate}</span>` : ''}
                ${dueDate ? `<span class="task-due-date"><i class="fas fa-calendar"></i> 截止: ${dueDate}</span>` : ''}
            </div>
        </div>
        <div class="task-actions">
            <button class="edit-btn" onclick="editTask(${task.id})" title="编辑">
                <i class="fas fa-edit"></i>
            </button>
            <button class="delete-btn" onclick="deleteTask(${task.id})" title="删除">
                <i class="fas fa-trash"></i>
            </button>
        </div>
        <div class="drag-handle">
            <i class="fas fa-grip-vertical"></i>
        </div>
    `;
    
    taskList.appendChild(taskItem);
}

// ===== 任务编辑功能 =====
function editTask(taskId) {
    const task = allTasks.find(t => t.id === taskId);
    if (!task) return;
    
    const newContent = prompt('编辑任务内容:', task.content);
    if (newContent === null || newContent.trim() === '') return;
    
    const updateData = { content: newContent.trim() };
    
    fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(updatedTask => {
        fetchTasks();
    })
    .catch(error => {
        console.error('Error updating task:', error);
        alert('更新任务失败');
    });
}

// ===== 任务状态切换 =====
function toggleTaskCompletion(taskId) {
    const task = allTasks.find(t => t.id === taskId);
    if (!task) return;
    
    const updateData = { completed: !task.completed };
    
    fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(updatedTask => {
        fetchTasks();
        loadStatistics();
    })
    .catch(error => {
        console.error('Error updating task:', error);
        alert('更新任务状态失败');
    });
}

// ===== 任务删除 =====
function deleteTask(taskId) {
    if (!confirm('确定要删除这个任务吗？')) return;
    
    fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE'
    })
    .then(response => {
        if (response.ok) {
            fetchTasks();
            loadStatistics();
        }
    })
    .catch(error => {
        console.error('Error deleting task:', error);
        alert('删除任务失败');
    });
}

// ===== 批量操作功能 =====
function toggleTaskSelection(taskId) {
    const index = selectedTasks.indexOf(taskId);
    if (index > -1) {
        selectedTasks.splice(index, 1);
    } else {
        selectedTasks.push(taskId);
    }
    updateBatchButtons();
    updateSelectAllCheckbox();
}

function toggleSelectAll() {
    const isChecked = selectAllCheckbox.checked;
    const checkboxes = document.querySelectorAll('.task-checkbox');
    
    selectedTasks = [];
    checkboxes.forEach(checkbox => {
        checkbox.checked = isChecked;
        if (isChecked) {
            const taskId = parseInt(checkbox.closest('.task-item').dataset.id);
            selectedTasks.push(taskId);
        }
    });
    
    updateBatchButtons();
}

function updateSelectAllCheckbox() {
    const totalTasks = allTasks.length;
    const selectedCount = selectedTasks.length;
    
    if (selectedCount === 0) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = false;
    } else if (selectedCount === totalTasks) {
        selectAllCheckbox.indeterminate = false;
        selectAllCheckbox.checked = true;
    } else {
        selectAllCheckbox.indeterminate = true;
    }
}

function updateBatchButtons() {
    const hasSelection = selectedTasks.length > 0;
    batchCompleteBtn.disabled = !hasSelection;
    batchDeleteBtn.disabled = !hasSelection;
    
    if (hasSelection) {
        batchCompleteBtn.textContent = `批量完成 (${selectedTasks.length})`;
        batchDeleteBtn.textContent = `批量删除 (${selectedTasks.length})`;
    } else {
        batchCompleteBtn.textContent = '批量完成';
        batchDeleteBtn.textContent = '批量删除';
    }
}

function batchComplete() {
    if (selectedTasks.length === 0) return;
    
    const updateData = { task_ids: selectedTasks, completed: true };
    
    fetch('/api/tasks/batch', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(result => {
        selectedTasks = [];
        fetchTasks();
        loadStatistics();
    })
    .catch(error => {
        console.error('Error batch completing tasks:', error);
        alert('批量完成失败');
    });
}

function batchDelete() {
    if (selectedTasks.length === 0) return;
    
    if (!confirm(`确定要删除选中的 ${selectedTasks.length} 个任务吗？`)) return;
    
    fetch('/api/tasks/batch', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_ids: selectedTasks })
    })
    .then(response => {
        if (response.ok) {
            selectedTasks = [];
            fetchTasks();
            loadStatistics();
        }
    })
    .catch(error => {
        console.error('Error batch deleting tasks:', error);
        alert('批量删除失败');
    });
}

// ===== 搜索和过滤功能 =====
function applyFilters() {
    fetchTasks();
}

// ===== 拖拽排序功能 =====
function initializeSortable() {
    if (typeof Sortable === 'undefined') {
        console.warn('SortableJS not loaded');
        return;
    }
    
    sortable = Sortable.create(taskList, {
        handle: '.drag-handle',
        animation: 150,
        onEnd: function(evt) {
            const taskId = parseInt(evt.item.dataset.id);
            const newIndex = evt.newIndex;
            updateTaskOrder(taskId, newIndex);
        }
    });
}

function updateTaskOrder(taskId, newIndex) {
    const updateData = { order: newIndex };
    
    fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(updatedTask => {
        // 可以选择是否重新加载任务列表
        // fetchTasks();
    })
    .catch(error => {
        console.error('Error updating task order:', error);
        // 如果更新失败，重新加载任务列表恢复原始顺序
        fetchTasks();
    });
}

// ===== 统计功能 =====
function loadStatistics() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(stats => {
            updateStatisticsDisplay(stats);
        })
        .catch(error => {
            console.error('Error loading statistics:', error);
        });
}

function updateStatisticsDisplay(stats) {
    totalTasksSpan.textContent = stats.total_tasks;
    completedTasksSpan.textContent = stats.completed_tasks;
    pendingTasksSpan.textContent = stats.pending_tasks;
    completionRateSpan.textContent = stats.completion_rate + '%';
}

// ===== 辅助函数 =====
function showEmptyState() {
    emptyState.style.display = 'block';
}

function hideEmptyState() {
    emptyState.style.display = 'none';
}

// ===== 应用功能总结 =====
/*
这个增强版的待办事项应用包含以下功能：

1. 基础功能：
   - 添加、编辑、删除、完成任务
   - 任务持久化存储

2. 分类管理：
   - 创建、删除任务分类
   - 为任务分配分类

3. 任务属性：
   - 优先级设置（高、中、低）
   - 截止日期设置
   - 任务编辑（双击或点击编辑按钮）

4. 搜索和过滤：
   - 关键词搜索
   - 按完成状态过滤
   - 按分类过滤
   - 按优先级过滤

5. 批量操作：
   - 全选/取消全选
   - 批量完成任务
   - 批量删除任务

6. 拖拽排序：
   - 使用SortableJS实现任务拖拽重排

7. 数据统计：
   - 任务总数、完成数、待处理数
   - 完成率计算

8. 用户体验优化：
   - 响应式设计
   - 图标支持（Font Awesome）
   - 友好的错误提示
   - 确认对话框防误操作
*/