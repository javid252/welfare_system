window.Components = window.Components || {};

window.Components.EmployeeSummary = {
    template: `
    <div>
        <h4 class="mb-4">خلاصه عملکرد من — سال {{ year }}</h4>
        <div v-if="loading" class="text-muted">در حال بارگذاری...</div>
        <div v-else class="row g-3">
            <div class="col-md-3">
                <div class="card metric-card border-primary">
                    <div class="card-body">
                        <div class="text-muted small">مجموع واحد کار خام</div>
                        <div class="fs-3 fw-bold">{{ fmt(summary.raw_swu_total) }}</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card border-success">
                    <div class="card-body">
                        <div class="text-muted small">مجموع واحد کار تعدیل‌شده</div>
                        <div class="fs-3 fw-bold">{{ fmt(summary.adjusted_swu_total) }}</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card border-info">
                    <div class="card-body">
                        <div class="text-muted small">امتیاز کیفیت (میانگین ممیزی)</div>
                        <div class="fs-3 fw-bold">{{ summary.average_quality_score ? fmt(summary.average_quality_score, 1) : '—' }}</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card border-warning">
                    <div class="card-body">
                        <div class="text-muted small">سهم تخمینی رفاهی</div>
                        <div class="fs-3 fw-bold">{{ summary.estimated_welfare_share ? fmt(summary.estimated_welfare_share, 0) + ' ریال' : 'محاسبه نشده' }}</div>
                    </div>
                </div>
            </div>
            <div class="col-12">
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between text-muted small mb-2">
                            <span>تعداد فعالیت‌های تایید شده: {{ summary.activity_count | faNum(0) }}</span>
                            <span>در انتظار تایید: {{ summary.pending_activity_count | faNum(0) }}</span>
                        </div>
                        <canvas id="trend-chart" height="90"></canvas>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `,
    data() {
        return {
            loading: true,
            year: new Date().getFullYear(),
            summary: {},
            chart: null,
        };
    },
    mounted() {
        this.load();
    },
    methods: {
        fmt(v, decimals) {
            return window.PersianUtils.toFaNumber(v, decimals);
        },
        async load() {
            this.loading = true;
            const [summaryRes, trendRes] = await Promise.all([
                api.get("dashboard/employee-summary/", { params: { year: this.year } }),
                api.get("dashboard/trends/", { params: { year: this.year } }),
            ]);
            this.summary = summaryRes.data;
            this.loading = false;
            this.$nextTick(() => this.renderChart(trendRes.data.monthly));
        },
        renderChart(monthly) {
            const ctx = document.getElementById("trend-chart");
            if (!ctx) return;
            if (this.chart) this.chart.destroy();
            this.chart = new Chart(ctx, {
                type: "line",
                data: {
                    labels: monthly.map(m => new Date(m.month).toLocaleDateString("fa-IR", { year: "numeric", month: "long" })),
                    datasets: [{
                        label: "واحد کار تعدیل‌شده ماهانه",
                        data: monthly.map(m => m.total_adjusted_swu),
                        borderColor: "#0d6efd",
                        backgroundColor: "rgba(13,110,253,0.15)",
                        tension: 0.3,
                        fill: true,
                    }],
                },
                options: { responsive: true, plugins: { legend: { display: false } } },
            });
        },
    },
};
