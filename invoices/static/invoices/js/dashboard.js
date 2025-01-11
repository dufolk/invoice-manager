// 图表主题色
const colors = ['#00C6FF', '#4CAF50', '#FFC107', '#FF5722', '#9C27B0'];

// 通用图表配置
const commonConfig = {
    backgroundColor: 'transparent',
    title: {
        textStyle: { 
            color: '#00C6FF',
            fontSize: 16,
            fontWeight: 'normal'
        }
    },
    tooltip: {
        backgroundColor: 'rgba(13, 25, 76, 0.8)',
        borderColor: '#00C6FF',
        textStyle: {
            color: '#fff'
        }
    }
};

// 初始化图表
const monthlyChart = echarts.init(document.getElementById('monthlyChart'));
const typeChart = echarts.init(document.getElementById('typeChart'));
const expenseTypeChart = echarts.init(document.getElementById('expenseTypeChart'));
const travelChart = echarts.init(document.getElementById('travelChart'));

// 月度趋势图（主图表）
monthlyChart.setOption({
    ...commonConfig,
    grid: {
        top: '10%',
        left: '3%',
        right: '3%',
        bottom: '3%',
        containLabel: true
    },
    xAxis: {
        type: 'category',
        data: monthlyLabels,
        axisLine: {
            lineStyle: { color: '#1E478F' }
        },
        axisLabel: { 
            color: '#7EAEFF',
            fontSize: 12,
            rotate: 30
        }
    },
    yAxis: {
        type: 'value',
        axisLine: {
            lineStyle: { color: '#1E478F' }
        },
        splitLine: {
            lineStyle: { color: 'rgba(30, 71, 143, 0.3)' }
        },
        axisLabel: { 
            color: '#7EAEFF',
            fontSize: 12
        }
    },
    series: [{
        data: monthlyData,
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: {
            color: '#00C6FF'
        },
        lineStyle: {
            width: 3,
            shadowColor: 'rgba(0, 198, 255, 0.3)',
            shadowBlur: 10
        },
        areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                offset: 0,
                color: 'rgba(0, 198, 255, 0.3)'
            }, {
                offset: 1,
                color: 'rgba(0, 198, 255, 0.1)'
            }])
        }
    }]
});

// 发票类型占比图
typeChart.setOption({
    ...commonConfig,
    series: [{
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '50%'],
        data: typeData,
        label: {
            color: '#7EAEFF'
        },
        itemStyle: {
            borderColor: '#081449',
            borderWidth: 2
        },
        emphasis: {
            itemStyle: {
                shadowBlur: 20,
                shadowColor: 'rgba(0, 198, 255, 0.5)'
            }
        }
    }]
});

// 费用类型分布图
expenseTypeChart.setOption({
    ...commonConfig,
    series: [{
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '50%'],
        data: expenseTypeData,
        label: {
            color: '#7EAEFF'
        },
        itemStyle: {
            borderColor: '#081449',
            borderWidth: 2
        },
        emphasis: {
            itemStyle: {
                shadowBlur: 20,
                shadowColor: 'rgba(0, 198, 255, 0.5)'
            }
        }
    }]
});

// 差旅费用构成图
travelChart.setOption({
    ...commonConfig,
    grid: {
        top: '15%',
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
    },
    xAxis: {
        type: 'category',
        data: travelLabels,
        axisLine: {
            lineStyle: {
                color: '#1E478F'
            }
        },
        axisLabel: { 
            color: '#7EAEFF',
            fontSize: 12
        }
    },
    yAxis: {
        type: 'value',
        axisLine: {
            lineStyle: {
                color: '#1E478F'
            }
        },
        splitLine: {
            lineStyle: {
                color: 'rgba(30, 71, 143, 0.3)'
            }
        },
        axisLabel: { 
            color: '#7EAEFF',
            fontSize: 12
        }
    },
    series: [{
        data: travelData,
        type: 'bar',
        barWidth: '40%',
        itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                offset: 0,
                color: 'rgba(0, 198, 255, 0.8)'
            }, {
                offset: 1,
                color: 'rgba(0, 198, 255, 0.3)'
            }]),
            borderRadius: [4, 4, 0, 0]
        }
    }]
});

// 响应式调整
window.addEventListener('resize', function() {
    monthlyChart.resize();
    typeChart.resize();
    expenseTypeChart.resize();
    travelChart.resize();
}); 