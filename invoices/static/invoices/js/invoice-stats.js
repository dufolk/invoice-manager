let personalChart = null;
let expenseChart = null;

function showPersonalStats() {
    const modal = document.getElementById('statsModal');
    const modalTitle = document.getElementById('modalTitle');
    const chartContainer = document.getElementById('statsChart');
    modalTitle.textContent = '个人月度报销统计';
    modal.style.display = 'block';
    
    try {
        if (!personalChart) {
            if (!echarts) {
                console.error('ECharts library not loaded');
                return;
            }
            personalChart = echarts.init(chartContainer);
        } else {
            personalChart.dispose();
            personalChart = echarts.init(chartContainer);
        }
        
        // 清空搜索框
        document.getElementById('personSearch').value = '';
        // 隐藏无数据提示
        document.getElementById('noDataTip').style.display = 'none';
        
        // 生成最近12个月的月份标签
        const months = [];
        const now = new Date();
        for (let i = 11; i >= 0; i--) {
            const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
            months.push(d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0'));
        }
        
        // 显示空的折线图框架
        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                show: false,
                backgroundColor: 'rgba(50, 50, 50, 0.9)',
                borderColor: 'rgba(126, 174, 255, 0.2)',
                textStyle: {
                    color: '#fff'
                }
            },
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: months,
                axisLabel: {
                    color: '#7EAEFF',
                    rotate: 45
                },
                axisLine: {
                    lineStyle: {
                        color: 'rgba(126, 174, 255, 0.2)'
                    }
                },
                splitLine: {
                    show: false
                }
            },
            yAxis: {
                type: 'value',
                axisLabel: {
                    color: '#7EAEFF',
                    formatter: value => '¥' + value.toFixed(2)
                },
                splitLine: {
                    lineStyle: {
                        color: 'rgba(126, 174, 255, 0.1)'
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: 'rgba(126, 174, 255, 0.2)'
                    }
                }
            }
        };
        personalChart.setOption(option);
    } catch (error) {
        console.error('Error initializing chart:', error);
        chartContainer.innerHTML = '<div class="error-message">图表加载失败</div>';
    }
}

function searchPersonStats() {
    const searchValue = document.getElementById('personSearch').value.trim();
    const noDataTip = document.getElementById('noDataTip');
    
    if (!searchValue) {
        noDataTip.style.display = 'block';
        noDataTip.textContent = '请输入报销人姓名';
        return;
    }
    
    if (!personalChart) {
        personalChart = echarts.init(document.getElementById('statsChart'));
    } else {
        personalChart.dispose();
        personalChart = echarts.init(document.getElementById('statsChart'));
    }
    
    // 获取统计数据
    showLoading(personalChart);
    fetch(`/manage/stats/personal/?search=${encodeURIComponent(searchValue)}`)
        .then(response => response.json())
        .then(data => {
            hideLoading(personalChart);
            if (!data.series || data.series.length === 0) {
                noDataTip.style.display = 'block';
                noDataTip.textContent = '未找到相关数据，请尝试其他搜索条件';
                return;
            }
            
            noDataTip.style.display = 'none';
            const option = {
                backgroundColor: 'transparent',
                tooltip: {
                    trigger: 'axis',
                    backgroundColor: 'rgba(50, 50, 50, 0.9)',
                    borderColor: 'rgba(126, 174, 255, 0.2)',
                    textStyle: {
                        color: '#fff'
                    },
                    axisPointer: {
                        type: 'line',
                        lineStyle: {
                            color: 'rgba(126, 174, 255, 0.5)'
                        }
                    }
                },
                legend: {
                    data: data.series.map(s => s.name),
                    textStyle: {
                        color: '#7EAEFF'
                    },
                    top: 10
                },
                grid: {
                    left: '3%',
                    right: '4%',
                    bottom: '3%',
                    containLabel: true
                },
                xAxis: {
                    type: 'category',
                    data: data.months,
                    axisLabel: {
                        color: '#7EAEFF',
                        rotate: 45
                    },
                    axisLine: {
                        lineStyle: {
                            color: 'rgba(126, 174, 255, 0.2)'
                        }
                    },
                    splitLine: {
                        show: false
                    }
                },
                yAxis: {
                    type: 'value',
                    axisLabel: {
                        color: '#7EAEFF',
                        formatter: value => '¥' + value.toFixed(2)
                    },
                    splitLine: {
                        lineStyle: {
                            color: 'rgba(126, 174, 255, 0.1)'
                        }
                    },
                    axisLine: {
                        lineStyle: {
                            color: 'rgba(126, 174, 255, 0.2)'
                        }
                    }
                },
                series: data.series.map(s => ({
                    ...s,
                    smooth: true,
                    symbol: 'circle',
                    symbolSize: 8,
                    lineStyle: {
                        width: 3
                    },
                    itemStyle: {
                        borderWidth: 2
                    },
                    emphasis: {
                        focus: 'series',
                        itemStyle: {
                            borderWidth: 3,
                            borderColor: '#fff',
                            shadowBlur: 10,
                            shadowColor: 'rgba(126, 174, 255, 0.5)'
                        }
                    }
                }))
            };
            personalChart.setOption(option);
        })
        .catch(error => {
            hideLoading(personalChart);
            console.error('Error:', error);
            alert(error.message || '获取发票详情失败');
            
            // 如果是因为发票不存在，关闭模态框
            const modal = document.getElementById('invoiceDetailModal');
            if (modal.style.display === 'block') {
                modal.style.display = 'none';
            }
        });
}

// 支持回车键搜索
document.getElementById('personSearch')?.addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
        searchPersonStats();
    }
});

function showExpenseTypeStats() {
    const modal = document.getElementById('expenseTypeModal');
    const chartContainer = document.getElementById('expenseTypeChart');
    modal.style.display = 'block';
    
    try {
        if (!expenseChart) {
            if (!echarts) {
                console.error('ECharts library not loaded');
                return;
            }
            expenseChart = echarts.init(chartContainer);
        } else {
            expenseChart.dispose();
            expenseChart = echarts.init(chartContainer);
        }
        
        fetch('/manage/stats/expense-type/')
            .then(response => response.json())
            .then(data => {
                const option = {
                    backgroundColor: 'transparent',
                    tooltip: {
                        trigger: 'item',
                        formatter: '{b}: {c} ({d}%)',
                        backgroundColor: 'rgba(50, 50, 50, 0.9)',
                        borderColor: 'rgba(126, 174, 255, 0.2)',
                        textStyle: {
                            color: '#fff'
                        }
                    },
                    series: [{
                        type: 'pie',
                        radius: ['40%', '70%'],
                        avoidLabelOverlap: false,
                        itemStyle: {
                            borderRadius: 10,
                            borderColor: 'rgba(30, 30, 45, 0.8)',
                            borderWidth: 2
                        },
                        label: {
                            show: true,
                            position: 'outer',
                            color: '#7EAEFF',
                            formatter: '{b}\n{d}%'
                        },
                        emphasis: {
                            label: {
                                show: true,
                                fontSize: '16',
                                fontWeight: 'bold'
                            },
                            itemStyle: {
                                shadowBlur: 10,
                                shadowColor: 'rgba(126, 174, 255, 0.5)'
                            }
                        },
                        labelLine: {
                            show: true,
                            length: 15,
                            length2: 10,
                            lineStyle: {
                                color: 'rgba(126, 174, 255, 0.3)'
                            }
                        },
                        data: data
                    }]
                };
                expenseChart.setOption(option);
            });
    } catch (error) {
        console.error('Error initializing chart:', error);
        chartContainer.innerHTML = '<div class="error-message">图表加载失败</div>';
    }
}

function closeExpenseTypeModal() {
    document.getElementById('expenseTypeModal').style.display = 'none';
    if (expenseChart) {
        expenseChart.dispose();
        expenseChart = null;
    }
}

function closeModal() {
    document.getElementById('statsModal').style.display = 'none';
    if (personalChart) {
        personalChart.dispose();
        personalChart = null;
    }
    if (expenseChart) {
        expenseChart.dispose();
        expenseChart = null;
    }
}

// 修改点击模态框外部关闭的事件
window.onclick = function(event) {
    const statsModal = document.getElementById('statsModal');
    const expenseTypeModal = document.getElementById('expenseTypeModal');
    const invoiceDetailModal = document.getElementById('invoiceDetailModal');
    
    if (event.target == statsModal) {
        closeModal();
    } else if (event.target == expenseTypeModal) {
        closeExpenseTypeModal();
    } else if (event.target == invoiceDetailModal) {
        closeInvoiceDetail();
    }
}

// 窗口大小改变时重绘图表
window.addEventListener('resize', function() {
    if (personalChart) {
        personalChart.resize();
    }
    if (expenseChart) {
        expenseChart.resize();
    }
});

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
            if (data.file_url) {
                const fileExt = data.file_url.split('.').pop().toLowerCase();
                
                if (['jpg', 'jpeg', 'png'].includes(fileExt)) {
                    filePreviewDiv.innerHTML = `
                        <img src="${data.file_url}" alt="发票图片" style="max-width: 100%; max-height: 500px;">
                    `;
                } else if (fileExt === 'pdf') {
                    filePreviewDiv.innerHTML = `
                        <embed src="${data.file_url}" type="application/pdf" width="100%" height="500px">
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

// 修改表格行点击事件的处理
document.addEventListener('DOMContentLoaded', function() {
    // 处理删除按钮点击
    document.querySelectorAll('.btn-icon.delete').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();  // 阻止事件冒泡，避免触发行点击事件
        });
    });

    // 处理编辑按钮点击
    document.querySelectorAll('.btn-icon[title="编辑"]').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();  // 阻止事件冒泡，避免触发行点击事件
        });
    });

    // 给表格行添加点击事件
    const invoiceRows = document.querySelectorAll('tr[data-invoice-id]');
    invoiceRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // 如果点击的是删除按钮或编辑按钮或其父元素，不显示详情
            if (e.target.closest('.btn-icon')) {
                return;
            }
            const invoiceId = this.dataset.invoiceId;
            showInvoiceDetail(invoiceId);
        });
        row.style.cursor = 'pointer';
    });
});

// 添加错误样式
const style = document.createElement('style');
style.textContent = `
    .error-message {
        color: #ff4444;
        text-align: center;
        padding: 20px;
        font-size: 14px;
    }
`;
document.head.appendChild(style); 

// 在图表加载前显示加载动画
function showLoading(chart) {
    if (chart) {
        chart.showLoading({
            text: '加载中...',
            color: '#7EAEFF',
            textColor: '#7EAEFF',
            maskColor: 'rgba(255, 255, 255, 0.8)',
            zlevel: 0
        });
    }
}

// 在数据加载完成后隐藏加载动画
function hideLoading(chart) {
    if (chart) {
        chart.hideLoading();
    }
} 