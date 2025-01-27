// 将 loadData 函数移到全局作用域
window.loadData = function(page = 1) {
    // 获取所有筛选参数
    const filterForm = document.querySelector('.filter-form');
    const formData = new FormData(filterForm);
    const searchParams = new URLSearchParams(formData);

    // 添加排序和分页参数
    searchParams.set('sort_by', window.currentSort);
    searchParams.set('order', window.currentOrder);
    searchParams.set('page', page);

    fetch(`${INVOICE_DATA_URL}?${searchParams.toString()}`)
        .then(response => response.json())
        .then(data => {
            updateTable(data);
            // 更新 URL，但不刷新页面
            const newUrl = `${window.location.pathname}?${searchParams.toString()}`;
            window.history.pushState({}, '', newUrl);
        })
        .catch(error => console.error('Error:', error));
}
document.getElementById('delete-btn').addEventListener('click', function() {
    // 获取所有选中的发票复选框
    const selectedInvoices = Array.from(document.querySelectorAll('.invoice-checkbox:checked')).map(checkbox => checkbox.value);
    
    // 如果没有选中任何发票，提示用户
    if (selectedInvoices.length === 0) {
        alert('请至少选择一张发票进行删除。');
        return;
    }

    // 确认删除操作
    if (confirm('确定要删除选中的发票吗？此操作不可恢复！')) {
        // 发送删除请求
        fetch('/manage/invoices/batch-delete/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ invoice_ids: selectedInvoices })
        })
        .then(response => {
            if (response.ok) {
                // 删除成功后重新加载数据
                loadData();
            } else {
                alert('删除失败，请重试。');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('删除失败，请重试。');
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const tableBody = document.querySelector('table tbody');
    const sortLinks = document.querySelectorAll('th a[data-sort]');
    // 将排序变量也移到全局
    window.currentSort = 'invoice_date';
    window.currentOrder = 'desc';

    // 更新表格内容
    window.updateTable = function(data) {
        tableBody.innerHTML = '';
        
        if (data.invoices.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.innerHTML = `
                <td colspan="9" class="empty-message">
                    <div class="no-data">
                        <span class="icon">📭</span>
                        <p>暂无发票记录</p>
                    </div>
                </td>
            `;
            tableBody.appendChild(emptyRow);
        } else {
            data.invoices.forEach(invoice => {
                const row = document.createElement('tr');
                row.className = invoice.has_potential_issue ? 'has-issue clickable-row' : 'no-issue clickable-row';
                row.dataset.invoiceId = invoice.id;
                
                // 获取状态显示样式
                const statusClass = getStatusClass(invoice.reimbursement_status);
                const statusText = getStatusText(invoice.reimbursement_status);
                
                row.innerHTML = `
                    <td>
                        <input type="checkbox" class="invoice-checkbox" value="${invoice.id}">
                    </td>
                    <td>${invoice.invoice_number}</td>
                    <td>${invoice.invoice_type}</td>
                    <td>${invoice.expense_type}</td>
                    <td>¥${invoice.amount.toFixed(2)}</td>
                    <td>${invoice.reimbursement_person}</td>
                    <td>${invoice.invoice_date}</td>
                    <td class="status ${statusClass}">${statusText}</td>
                    <td class="actions">
                        <a href="${INVOICE_EDIT_URL}${invoice.id}/edit/" class="btn-icon" title="编辑">✏️</a>
                        <a href="#" onclick="confirmDelete(${invoice.id}); return false;" class="btn-icon delete" title="删除">🗑️</a>
                    </td>
                `;
                
                // 添加点击事件
                row.addEventListener('click', function(e) {
                    // 如果点击的是按钮或复选框，不触发行点击事件
                    if (e.target.matches('button, a, input[type="checkbox"]') || 
                        e.target.closest('button, a')) {
                        return;
                    }
                    showInvoiceDetail(invoice.id);
                });
                
                tableBody.appendChild(row);
            });
        }

        // 更新总金额显示
        document.querySelector('.amount-total strong').textContent = 
            `¥${data.total_amount.toFixed(2)}`;

        // 更新分页状态
        updatePagination(data);

        // 重新绑定复选框事件监听器
        initializeCheckboxes();
    }

    // 更新分页控件
    function updatePagination(data) {
        let pagination = document.querySelector('.pagination');
        
        // 如果分页容器不存在，创建一个
        if (!pagination) {
            pagination = document.createElement('div');
            pagination.className = 'pagination';
            tableBody.parentElement.parentElement.appendChild(pagination);
            
            // 添加分页事件监听
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

    // 为所有筛选控件添加 change 事件监听
    function initializeFilters() {
        const filterForm = document.querySelector('.filter-form');
        const filterInputs = filterForm.querySelectorAll('input, select');

        filterInputs.forEach(input => {
            input.addEventListener('change', function() {
                loadData(1); // 重置到第一页
            });
        });

        // 搜索框添加防抖
        const searchInput = filterForm.querySelector('input[name="search"]');
        if (searchInput) {
            let debounceTimer;
            searchInput.addEventListener('input', function() {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    loadData(1);
                }, 300); // 300ms 延迟
            });
        }

        // 表单提交事件
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            loadData(1);
        });
    }

    // 绑定排序事件
    sortLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const sortBy = this.dataset.sort;
            
            if (window.currentSort === sortBy) {
                window.currentOrder = window.currentOrder === 'asc' ? 'desc' : 'asc';
            } else {
                window.currentSort = sortBy;
                window.currentOrder = 'desc';
            }

            // 更新排序图标
            sortLinks.forEach(l => {
                l.classList.remove('asc', 'desc');
            });
            this.classList.add(window.currentOrder);

            loadData();
        });
    });

    // 初始化筛选功能
    initializeFilters();

    // 页面加载时立即加载数据
    loadData();

    // 将复选框相关的初始化逻辑封装成独立函数
    function initializeCheckboxes() {
        // 处理全选复选框
        const selectAll = document.getElementById('select-all');
        selectAll.checked = false; // 重置全选状态

        // 为所有复选框添加事件监听器
        document.querySelectorAll('.invoice-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                updateDeleteButtonState();
                
                // 检查是否所有复选框都被选中
                const allCheckboxes = document.querySelectorAll('.invoice-checkbox');
                const allChecked = Array.from(allCheckboxes).every(cb => cb.checked);
                selectAll.checked = allChecked;
            });
        });

        // 重新绑定全选复选框事件
        selectAll.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.invoice-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked; // 设置每个复选框的选中状态
            });
            updateDeleteButtonState(); // 更新删除按钮状态
        });

        // 更新删除按钮状态
        updateDeleteButtonState();
    }

    // 更新删除按钮状态的函数
    function updateDeleteButtonState() {
        const checkboxes = document.querySelectorAll('.invoice-checkbox');
        const deleteButton = document.getElementById('delete-btn');
        const anyChecked = Array.from(checkboxes).some(checkbox => checkbox.checked);
        deleteButton.disabled = !anyChecked; // 如果没有选中任何复选框，则禁用删除按钮
    }

    // 初始化复选框
    initializeCheckboxes();
});

// 添加发票详情相关函数
window.showInvoiceDetail = function(invoiceId) {
    fetch(`${INVOICE_DETAIL_URL}${invoiceId}/detail/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('detailInvoiceNumber').textContent = data.invoice_number;
            document.getElementById('detailInvoiceType').textContent = data.invoice_type_display;
            document.getElementById('detailExpenseType').textContent = data.expense_type;
            document.getElementById('detailAmount').textContent = `¥${data.amount.toFixed(2)}`;
            document.getElementById('detailPerson').textContent = data.reimbursement_person;
            document.getElementById('detailDate').textContent = data.invoice_date;
            document.getElementById('detailDetails').textContent = data.details || '-';
            document.getElementById('detailRemarks').textContent = data.remarks || '-';
            
            // 处理发票文件预览
            handleFilePreview(data);
            
            // 处理附件信息
            if (data.attachment_url) {
                document.getElementById('attachmentInfo').innerHTML = `
                    <a href="${data.attachment_url}" target="_blank">${data.attachment_name}</a>
                `;
            } else {
                document.getElementById('attachmentInfo').innerHTML = '<p>无附件</p>';
            }
            
            // 显示问题图标（如果有）
            const issueIcon = document.getElementById('detailIssue');
            if (data.has_potential_issue) {
                issueIcon.textContent = '⚠️';
                issueIcon.title = '可能存在问题';
            } else {
                issueIcon.textContent = '';
                issueIcon.title = '';
            }
            
            document.getElementById('invoiceDetailModal').style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('加载发票详情失败');
        });
}

window.closeInvoiceDetail = function() {
    document.getElementById('invoiceDetailModal').style.display = 'none';
}

// 添加删除确认函数
window.confirmDelete = function(invoiceId) {
    if (confirm('确定要删除这张发票吗？此操作不可恢复！')) {
        fetch(`${INVOICE_DELETE_URL}${invoiceId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        }).then(response => {
            if (response.ok) {
                window.loadData(); // 使用全局的 loadData
            } else {
                alert('删除失败');
            }
        }).catch(error => {
            console.error('Error:', error);
            alert('删除失败');
        });
    }
}

// 添加状态样式和文本转换函数
function getStatusClass(status) {
    const statusClasses = {
        'NOT_SUBMITTED': 'status-not-submitted',
        'PENDING': 'status-pending',
        'NOT_TRANSFERRED': 'status-not-transferred',
        'TRANSFERRED': 'status-transferred'
    };
    return statusClasses[status] || '';
}

function getStatusText(status) {
    const statusTexts = {
        'NOT_SUBMITTED': '未提交',
        'PENDING': '未报销',
        'NOT_TRANSFERRED': '未转入管理员账户',
        'TRANSFERRED': '已转入管理员账户'
    };
    return statusTexts[status] || status;
}

// 处理文件预览
function handleFilePreview(data) {
    const filePreviewDiv = document.getElementById('filePreview');
    const container = filePreviewDiv.closest('.detail-image');

    if (data.file_url) {
        const fileExt = data.file_url.split('.').pop().toLowerCase();
        
        if (['jpg', 'jpeg', 'png'].includes(fileExt)) {
            container.className = 'detail-image image-container';
            filePreviewDiv.innerHTML = `
                <img src="${data.file_url}" alt="发票图片">
            `;
        } else if (fileExt === 'pdf') {
            container.className = 'detail-image pdf-container';
            filePreviewDiv.innerHTML = `
                <embed src="${data.file_url}#toolbar=0&navpanes=0" type="application/pdf">
                <p class="pdf-fallback" style="display: none;">
                    <a href="${data.file_url}" target="_blank" class="btn btn-primary">
                        <i class="fas fa-file-pdf"></i> 在新窗口打开 PDF
                    </a>
                </p>
            `;
            
            const embed = filePreviewDiv.querySelector('embed');
            embed.onerror = function() {
                filePreviewDiv.querySelector('.pdf-fallback').style.display = 'block';
                embed.style.display = 'none';
            };
        }
    } else {
        container.className = 'detail-image empty-container';
        filePreviewDiv.innerHTML = `
            <div class="no-file-message">未上传发票文件</div>
        `;
    }
}

