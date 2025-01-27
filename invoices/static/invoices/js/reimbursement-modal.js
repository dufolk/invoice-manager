document.addEventListener('DOMContentLoaded', function() {
    window.showNewReimbursementModal = function() {
        const modal = document.getElementById('newReimbursementModal');
        const form = document.getElementById('reimbursementForm');
        
        // 重置表单
        form.reset();
        
        // 加载未报账的发票列表
        loadUnreimbursedInvoices();
        
        // 显示模态框
        modal.style.display = 'block';
    }

    window.closeNewReimbursementModal = function() {
        document.getElementById('newReimbursementModal').style.display = 'none';
    }

    window.markAsCompleted = function(recordId) {
        if (!confirm('确定要将此报账记录标记为已报账吗？')) {
            return;
        }

        fetch(`/manage/reimbursement/${recordId}/complete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.loadData(); // 使用全局的 loadData 函数
            } else {
                alert(data.error || '操作失败');
            }
        });
    }

    // 加载未报账的发票列表
    function loadUnreimbursedInvoices() {
        fetch('/manage/reimbursement/unreimbursed-invoices/')
            .then(response => response.json())
            .then(data => {
                const invoiceSelector = document.querySelector('.invoice-selector');
                if (data.invoices.length === 0) {
                    invoiceSelector.innerHTML = '<p class="no-data">暂无未报账的发票</p>';
                    return;
                }

                let html = '<div class="table-responsive"><table><thead><tr>' +
                    '<th width="40"><input type="checkbox" id="select-all-invoices"></th>' +
                    '<th>发票号</th>' +
                    '<th>类型</th>' +
                    '<th>费用类型</th>' +
                    '<th>金额</th>' +
                    '<th>报销人</th>' +
                    '<th>发票日期</th>' +
                    '</tr></thead><tbody>';

                data.invoices.forEach(invoice => {
                    html += `
                        <tr>
                            <td>
                                <input type="checkbox" name="invoice_ids[]" value="${invoice.id}" class="invoice-checkbox">
                            </td>
                            <td>${invoice.invoice_number}</td>
                            <td>${invoice.invoice_type_display}</td>
                            <td>${invoice.expense_type_name}</td>
                            <td>¥${invoice.amount.toFixed(2)}</td>
                            <td>${invoice.reimbursement_person}</td>
                            <td>${invoice.invoice_date}</td>
                        </tr>
                    `;
                });

                html += '</tbody></table></div>';
                invoiceSelector.innerHTML = html;

                // 绑定全选功能
                const selectAll = document.getElementById('select-all-invoices');
                const checkboxes = document.querySelectorAll('.invoice-checkbox');
                
                selectAll.addEventListener('change', function() {
                    checkboxes.forEach(checkbox => {
                        checkbox.checked = this.checked;
                    });
                });
            });
    }

    // 绑定表单提交事件
    const reimbursementForm = document.getElementById('reimbursementForm');
    if (reimbursementForm) {
        reimbursementForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => {
                if (response.ok) {
                    closeNewReimbursementModal();
                    window.loadData(); // 使用全局的 loadData 函数
                } else {
                    alert('提交失败');
                }
            });
        });
    }
}); 