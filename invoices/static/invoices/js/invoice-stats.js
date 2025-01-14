let personalChart = null;
let expenseChart = null;

// 个人统计相关函数
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
                show: false
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
                }
            },
            series: []
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

// 费用类型统计相关函数
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
        
        showLoading(expenseChart);
        fetch('/manage/stats/expense-type/')
            .then(response => response.json())
            .then(data => {
                hideLoading(expenseChart);
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
                            }
                        },
                        data: data
                    }]
                };
                expenseChart.setOption(option);
            })
            .catch(error => {
                hideLoading(expenseChart);
                console.error('Error:', error);
                chartContainer.innerHTML = '<div class="error-message">数据加载失败</div>';
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
}

// 工具函数
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

function hideLoading(chart) {
    if (chart) {
        chart.hideLoading();
    }
}

// 事件监听
window.addEventListener('resize', function() {
    if (personalChart) {
        personalChart.resize();
    }
    if (expenseChart) {
        expenseChart.resize();
    }
});

// 支持回车键搜索
document.getElementById('personSearch')?.addEventListener('keyup', function(event) {
    if (event.key === 'Enter') {
        searchPersonStats();
    }
}); 