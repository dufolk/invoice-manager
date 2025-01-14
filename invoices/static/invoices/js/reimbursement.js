function showNewReimbursementModal() {
    const modal = document.getElementById('newReimbursementModal');
    modal.classList.add('show');
    loadUnreimbursedInvoices();
}

function closeNewReimbursementModal() {
    const modal = document.getElementById('newReimbursementModal');
    modal.classList.remove('show');
}

async function loadUnreimbursedInvoices() {
    try {
        const response = await fetch('{% url "invoices:manage_unreimbursed_invoices" %}');
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
    // 实现查看报账详情的功能
}

async function markAsCompleted(id) {
    if (!confirm('确定将此记录标记为已报账？')) return;
    
    try {
        const response = await fetch(`{% url "invoices:manage_reimbursement_complete" pk=0 %}`.replace('0', id));
        
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