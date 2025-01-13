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
    // ... 搜索个人统计的代码 ...
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