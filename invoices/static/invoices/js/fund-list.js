document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.querySelector('table tbody');
    const sortLinks = document.querySelectorAll('th a[data-sort]');
    let currentSort = 'record_date';
    let currentOrder = 'desc';
    let currentRecordId = null;

    // 更新表格内容
    function updateTable(data) {
        tableBody.innerHTML = '';
        
        if (data.records.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = `
                <td colspan="7" class="empty-message">
                    <div class="no-data">
                        <span class="icon">📭</span>
                        <p>暂无经费记录</p>
                    </div>
                </td>
            `;
            tableBody.appendChild(emptyRow);
        } else {
            data.records.forEach(record => {
                const row = document.createElement('tr');
                row.dataset.recordId = record.id;
                row.innerHTML = `
                    <td>
                        <input type="checkbox" class="record-checkbox" value="${record.id}">
                    </td>
                    <td>${record.record_date}</td>
                    <td>${record.record_type}</td>
                    <td class="${record.amount < 0 ? 'text-danger' : 'text-success'}">
                        ¥${record.amount.toFixed(2)}
                    </td>
                    <td>¥${record.balance.toFixed(2)}</td>
                    <td class="description-cell" onclick="showDescription(this)">
                        <div class="description-preview">${record.description.length > 30 ? record.description.substring(0, 30) + '...' : record.description}</div>
                        <div class="description-full" style="display:none;">${record.description}</div>
                    </td>
                    <td class="actions">
                        <button class="btn-icon" onclick="showEditModal(${record.id})" title="编辑">
                            ✏️
                        </button>
                        <button class="btn-icon delete" onclick="showDeleteConfirm(${record.id})" title="删除">
                            🗑️
                        </button>
                    </td>
                `;
                tableBody.appendChild(row);
            });
        }

        // 更新余额显示
        document.querySelector('.balance-total strong').textContent = 
            `¥${data.current_balance.toFixed(2)}`;

        // 更新分页状态
        updatePagination(data);
        
        // 重新绑定复选框事件
        initializeCheckboxes();
    }

    // 更新分页控件
    function updatePagination(data) {
        let pagination = document.querySelector('.pagination');
        
        if (!pagination) {
            pagination = document.createElement('div');
            pagination.className = 'pagination';
            tableBody.parentElement.parentElement.appendChild(pagination);
            
            pagination.addEventListener('click', function(e) {
                if (e.target.matches('a[data-page]')) {
                    e.preventDefault();
                    const page = e.target.dataset.page;
                    loadData(page);
                }
            });
        }

        pagination.innerHTML = '';
        
        if (data.has_previous) {
            pagination.innerHTML += `
                <a href="#" class="btn" data-page="1">首页</a>
                <a href="#" class="btn" data-page="${data.page - 1}">上一页</a>
            `;
        }

        pagination.innerHTML += `
            <span class="current-page">
                第 ${data.page} 页，共 ${data.total_pages} 页
            </span>
        `;

        if (data.has_next) {
            pagination.innerHTML += `
                <a href="#" class="btn" data-page="${data.page + 1}">下一页</a>
                <a href="#" class="btn" data-page="${data.total_pages}">末页</a>
            `;
        }
    }

    // 加载数据
    function loadData(page = 1) {
        // 获取所有筛选参数
        const filterForm = document.querySelector('.filter-form');
        const formData = new FormData(filterForm);
        const searchParams = new URLSearchParams(formData);

        // 添加排序和分页参数
        searchParams.set('sort_by', currentSort);
        searchParams.set('order', currentOrder);
        searchParams.set('page', page);

        // 处理日期参数
        const date = formData.get('date');
        if (date) {
            searchParams.set('date', date);
        }

        fetch(`${FUND_DATA_URL}?${searchParams.toString()}`)
            .then(response => response.json())
            .then(data => {
                updateTable(data);
                const newUrl = `${window.location.pathname}?${searchParams.toString()}`;
                window.history.pushState({}, '', newUrl);
            })
            .catch(error => console.error('Error:', error));
    }

    // 初始化筛选器
    function initializeFilters() {
        const filterForm = document.querySelector('.filter-form');
        const filterInputs = filterForm.querySelectorAll('input, select');

        filterInputs.forEach(input => {
            if (input.type === 'text') {
                // 为搜索框添加防抖
                let debounceTimer;
                input.addEventListener('input', function() {
                    clearTimeout(debounceTimer);
                    debounceTimer = setTimeout(() => {
                        loadData(1);
                    }, 300);
                });
            } else {
                // 其他输入框直接触发
                input.addEventListener('change', function() {
                    loadData(1);
                });
            }
        });
    }

    // 初始化复选框
    function initializeCheckboxes() {
        const selectAll = document.getElementById('select-all');
        const checkboxes = document.querySelectorAll('.record-checkbox');
        
        selectAll.addEventListener('change', function() {
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateDeleteButton();
        });

        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateDeleteButton);
        });
    }

    // 更新删除按钮状态
    function updateDeleteButton() {
        const checkedBoxes = document.querySelectorAll('.record-checkbox:checked');
        const deleteBtn = document.getElementById('delete-btn');
        deleteBtn.disabled = checkedBoxes.length === 0;
    }

    // 绑定排序事件
    sortLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const sortBy = this.dataset.sort;
            
            if (currentSort === sortBy) {
                currentOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort = sortBy;
                currentOrder = 'desc';
            }

            sortLinks.forEach(l => {
                l.classList.remove('asc', 'desc');
            });
            this.classList.add(currentOrder);

            loadData();
        });
    });

    // 添加模态框相关函数
    window.showAddModal = function() {
        currentRecordId = null;
        document.getElementById('modalTitle').textContent = '记录经费变动';
        document.getElementById('fundForm').reset();
        document.getElementById('record_date').value = new Date().toISOString().split('T')[0];
        document.getElementById('fundModal').style.display = 'block';
    }

    window.showEditModal = function(recordId) {
        currentRecordId = recordId;
        document.getElementById('modalTitle').textContent = '编辑经费记录';
        
        fetch(`/manage/fund/${recordId}/edit/`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('recordId').value = data.id;
                document.getElementById('record_type').value = data.record_type;
                document.getElementById('amount').value = data.amount;
                document.getElementById('description').value = data.description;
                document.getElementById('record_date').value = data.record_date;
                document.getElementById('fundModal').style.display = 'block';
            });
    }

    window.closeModal = function() {
        document.getElementById('fundModal').style.display = 'none';
    }

    window.handleSubmit = function(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const url = currentRecordId 
            ? `/manage/fund/${currentRecordId}/edit/`
            : '/manage/fund/add/';
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                closeModal();
                loadData(); // 使用 AJAX 重新加载数据而不是刷新页面
            } else {
                alert(data.error || '操作失败');
            }
        });
    }

    window.showDescription = function(cell) {
        const preview = cell.querySelector('.description-preview');
        const full = cell.querySelector('.description-full');
        
        if (preview.style.display !== 'none') {
            preview.style.display = 'none';
            full.style.display = 'block';
        } else {
            preview.style.display = 'block';
            full.style.display = 'none';
        }
    }

    window.showDeleteConfirm = function(recordId) {
        currentRecordId = recordId;
        document.getElementById('deleteModal').style.display = 'block';
    }

    window.closeDeleteModal = function() {
        document.getElementById('deleteModal').style.display = 'none';
    }

    window.confirmDelete = function() {
        if (!currentRecordId) return;
        
        fetch(`/manage/fund/${currentRecordId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => {
            if (response.ok) {
                closeDeleteModal();
                loadData(); // 使用 AJAX 重新加载数据
            } else {
                alert('删除失败');
            }
        });
    }

    // 绑定表单提交事件
    const fundForm = document.getElementById('fundForm');
    if (fundForm) {
        // 移除可能存在的旧事件监听器
        fundForm.removeEventListener('submit', handleSubmit);
        // 添加新的事件监听器
        fundForm.addEventListener('submit', handleSubmit);
    }

    // 初始化
    initializeFilters();
    loadData();
}); 