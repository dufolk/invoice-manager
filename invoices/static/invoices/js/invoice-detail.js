// 显示发票详情
function showInvoiceDetail(invoiceId) {
    // 如果传入的是 ID 字符串，直接使用
    const id = typeof invoiceId === 'object' ? invoiceId.invoice_id : invoiceId;
    
    fetch(`/manage/invoice/${id}/detail/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('发票不存在或已被删除');
            }
            return response.json();
        })
        .then(data => {
            if (!data) {
                throw new Error('无法获取发票数据');
            }
            
            // 填充基本信息
            document.getElementById('detailInvoiceNumber').textContent = data.invoice_number;
            document.getElementById('detailInvoiceType').textContent = data.invoice_type_display;
            document.getElementById('detailExpenseType').textContent = data.expense_type;
            document.getElementById('detailAmount').textContent = `¥${data.amount.toFixed(2)}`;
            document.getElementById('detailPerson').textContent = data.reimbursement_person;
            document.getElementById('detailDate').textContent = data.invoice_date;
            document.getElementById('detailDetails').textContent = data.details || '无';
            document.getElementById('detailRemarks').textContent = data.remarks || '无';
            
            // 处理文件预览
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

            document.getElementById('invoiceDetailModal').style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message || '获取发票详情失败');
            
            // 如果是因为发票不存在，关闭模态框
            const modal = document.getElementById('invoiceDetailModal');
            if (modal.style.display === 'block') {
                modal.style.display = 'none';
            }
        });
}

// 关闭发票详情模态框
function closeInvoiceDetail() {
    const modal = document.getElementById('invoiceDetailModal');
    if (modal) {
        modal.style.display = 'none';
        
        // 清空文件预览区域
        const filePreview = document.getElementById('filePreview');
        if (filePreview) {
            filePreview.innerHTML = '';
        }
    }
}

// 初始化发票详情功能
document.addEventListener('DOMContentLoaded', function() {
    // 处理删除按钮点击
    document.querySelectorAll('.btn-icon.delete').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();  // 阻止事件冒泡，避免触发行点击事件
        });
    });

    // 给表格行添加点击事件
    const invoiceRows = document.querySelectorAll('tr[data-invoice-id]');
    invoiceRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // 如果点击的是删除按钮或其父元素，不显示详情
            if (e.target.closest('.btn-icon.delete')) {
                return;
            }
            const invoiceId = this.dataset.invoiceId;
            showInvoiceDetail(invoiceId);
        });
        row.style.cursor = 'pointer';
    });
});

// 添加图片加载完成后的处理函数
function adjustImageContainer(img) {
    const container = img.closest('.detail-image');
    if (img.naturalWidth > img.naturalHeight) {
        container.classList.remove('portrait');
    } else {
        container.classList.add('portrait');
    }
} 