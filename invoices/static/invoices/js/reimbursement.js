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
        container.innerHTML = data.invoices.map(invoice => `
            <div class="invoice-item">
                <input type="checkbox" name="invoice_ids[]" value="${invoice.id}">
                <span>${invoice.invoice_number} - ¥${invoice.amount} - ${invoice.reimbursement_person}</span>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading invoices:', error);
    }
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