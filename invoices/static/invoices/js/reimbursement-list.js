document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.querySelector('table tbody');
    const sortLinks = document.querySelectorAll('th a[data-sort]');
    let currentSort = 'reimbursement_date';
    let currentOrder = 'desc';

    // 更新表格内容
    function updateTable(data) {
        tableBody.innerHTML = '';
        
        if (data.records.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = `
                <td colspan="7" class="empty-message">
                    <div class="no-data">
                        <span class="icon">📭</span>
                        <p>暂无报账记录</p>
                    </div>
                </td>
            `;
            tableBody.appendChild(emptyRow);
        } else {
            data.records.forEach(record => {
                const row = document.createElement('tr');
                row.className = 'clickable-row';
                row.dataset.recordId = record.id;
                row.innerHTML = `
                    <td>${record.reimbursement_date}</td>
                    <td>${record.record_type}</td>
                    <td>${record.invoice_count}</td>
                    <td>¥${record.total_amount.toFixed(2)}</td>
                    <td>
                        <span class="status-badge ${record.status_code.toLowerCase()}">
                            ${record.status}
                        </span>
                    </td>
                    <td>${record.remarks}</td>
                    <td class="actions">
                        ${record.status_code === 'SUBMITTED' ? 
                            `<button class="btn-icon" onclick="markAsCompleted(${record.id})" title="标记为已报账">✓</button>` 
                            : ''}
                    </td>
                `;
                // 添加点击事件
                row.addEventListener('click', function(e) {
                    // 如果点击的是按钮，不触发行点击事件
                    if (e.target.matches('button') || e.target.closest('button')) {
                        return;
                    }
                    window.location.href = `/manage/reimbursement/${record.id}/`;
                });
                tableBody.appendChild(row);
            });
        }

        // 更新分页状态
        updatePagination(data);
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

    // 将 loadData 函数暴露到全局
    window.loadData = function(page = 1) {
        const filterForm = document.querySelector('.filter-form');
        const formData = new FormData(filterForm);
        const searchParams = new URLSearchParams(formData);

        searchParams.set('sort_by', currentSort);
        searchParams.set('order', currentOrder);
        searchParams.set('page', page);

        fetch(`${REIMBURSEMENT_DATA_URL}?${searchParams.toString()}`)
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
            input.addEventListener('change', function() {
                loadData(1);
            });
        });
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

    // 初始化
    initializeFilters();
    loadData();
}); 