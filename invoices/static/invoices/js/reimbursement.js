let URLS = {
    reimbursementDetail: '/manage/reimbursement/0/',  // 修改为正确的URL路径
    unreimbursedInvoices: '/manage/reimbursement/unreimbursed-invoices/',
    reimbursementComplete: '/manage/reimbursement/0/complete/',
    removeInvoice: '/manage/reimbursement/0/remove-invoice/0/'
};

// 初始化 URL 配置
function initializeUrls(config) {
    URLS = { ...URLS, ...config };
}

function showNewReimbursementModal() {
    console.log('showNewReimbursementModal');
    const modal = document.getElementById('newReimbursementModal');
    modal.style.display = 'block';
    loadUnreimbursedInvoices();
}

function closeNewReimbursementModal() {
    const modal = document.getElementById('newReimbursementModal');
    modal.style.display = 'none';
}

async function loadUnreimbursedInvoices() {
    try {
        const response = await fetch(URLS.unreimbursedInvoices);
        const data = await response.json();
        
        const container = document.querySelector('.invoice-selector');
        container.innerHTML = `
            <div class="filter-bar" style="margin-bottom: 15px;">
                <input type="text" id="searchPerson" placeholder="搜索报销人..." 
                       onkeyup="filterInvoices()" class="search-input">
                <input type="date" id="searchDate" onchange="filterInvoices()" 
                       class="date-input">
            </div>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th width="40">
                                <input type="checkbox" id="selectAllUnreimbursed" onchange="toggleSelectAllUnreimbursed()">
                            </th>
                            <th>发票号</th>
                            <th>发票类型</th>
                            <th>费用类型</th>
                            <th>金额</th>
                            <th>报销人</th>
                            <th>发票日期</th>
                        </tr>
                    </thead>
                    <tbody id="invoiceTableBody">
                        ${data.invoices.map(invoice => `
                            <tr>
                                <td>
                                    <input type="checkbox" name="invoice_ids[]" value="${invoice.id}" 
                                           class="unreimbursed-checkbox">
                                </td>
                                <td>${invoice.invoice_number}</td>
                                <td>${invoice.invoice_type_display}</td>
                                <td>${invoice.expense_type_name}</td>
                                <td>¥${typeof invoice.amount === 'number' ? 
                                    invoice.amount.toFixed(2) : 
                                    parseFloat(invoice.amount).toFixed(2)}</td>
                                <td>${invoice.reimbursement_person}</td>
                                <td>${invoice.invoice_date}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } catch (error) {
        console.error('Error loading invoices:', error);
        container.innerHTML = '<div class="error-message">加载发票列表失败，请重试</div>';
    }
}

// 添加全选功能
function toggleSelectAllUnreimbursed() {
    const selectAll = document.getElementById('selectAllUnreimbursed');
    const checkboxes = document.querySelectorAll('.unreimbursed-checkbox');
    checkboxes.forEach(checkbox => checkbox.checked = selectAll.checked);
}

// 添加搜索过滤功能
function filterInvoices() {
    const searchPerson = document.getElementById('searchPerson').value.toLowerCase();
    const searchDate = document.getElementById('searchDate').value;
    const rows = document.querySelectorAll('#invoiceTableBody tr');

    rows.forEach(row => {
        const person = row.querySelector('td:nth-child(6)').textContent.toLowerCase();
        const date = row.querySelector('td:nth-child(7)').textContent;
        
        const matchPerson = person.includes(searchPerson);
        const matchDate = !searchDate || date === searchDate;

        row.style.display = (matchPerson && matchDate) ? '' : 'none';
    });
}

function viewReimbursement(id) {
    const url = URLS.reimbursementDetail.replace('0', id);
    window.location.href = url;
}

async function markAsCompleted(id) {
    if (!confirm('确定将此记录标记为已报账？')) return;
    
    try {
        const response = await fetch(URLS.reimbursementComplete.replace('0', id), {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        });
        
        if (response.ok) {
            window.location.reload();
        } else {
            alert('操作失败，请重试');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('操作失败，请重试');
    }
}

async function removeInvoice(invoiceId) {
    if (!confirm('确定要移除此发票吗？')) return;
    
    try {
        const response = await fetch(URLS.removeInvoice.replace('0', invoiceId), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        });
        
        if (response.ok) {
            window.location.reload();
        } else {
            const data = await response.json();
            alert('操作失败：' + (data.error || '请重试'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('操作失败，请重试');
    }
}

// 为表格行添加点击事件
document.addEventListener('DOMContentLoaded', function() {
    const rows = document.querySelectorAll('.clickable-row');
    rows.forEach(row => {
        row.addEventListener('click', function(e) {
            // 如果点击的是操作按钮，不触发行点击事件
            if (e.target.closest('.btn-icon')) return;
            
            const recordId = this.dataset.recordId;
            viewReimbursement(recordId);
        });
    });
}); 