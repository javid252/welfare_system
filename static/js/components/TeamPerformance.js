window.Components = window.Components || {};

window.Components.TeamPerformance = {
    template: `
    <div>
        <h4 class="mb-4">عملکرد تیم — سال {{ year }}</h4>
        <div class="row g-4 mb-4">
            <div class="col-lg-6">
                <div class="card"><div class="card-header fw-bold">توزیع واحد کار تعدیل‌شده (هیستوگرام)</div>
                    <div class="card-body"><canvas id="histogram-chart" height="180"></canvas></div>
                </div>
            </div>
            <div class="col-lg-6">
                <div class="card"><div class="card-header fw-bold">وضعیت وظایف تیم</div>
                    <div class="card-body"><canvas id="task-status-chart" height="180"></canvas></div>
                </div>
            </div>
        </div>
        <div class="card">
            <div class="card-header fw-bold">لیست اعضای تیم</div>
            <div class="table-responsive">
                <table class="table table-hover mb-0">
                    <thead><tr><th>کد پرسنلی</th><th>نام</th><th>سمت</th><th>واحد کار تعدیل‌شده</th><th>تعداد فعالیت</th></tr></thead>
                    <tbody>
                        <tr v-for="row in team" :key="row.employee.id">
                            <td>{{ row.employee.employee_code }}</td>
                            <td>{{ row.employee.full_name }}</td>
                            <td>{{ row.employee.position }}</td>
                            <td>{{ row.adjusted_swu | faNum(2) }}</td>
                            <td>{{ row.activity_count | faNum(0) }}</td>
                        </tr>
                        <tr v-if="!team.length"><td colspan="5" class="text-center text-muted py-3">عضوی یافت نشد.</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    `,
    data() {
        return { year: new Date().getFullYear(), team: [], histogram: [], taskStatusCounts: [] };
    },
    mounted() {
        this.load();
    },
    methods: {
        async load() {
            const res = await api.get("dashboard/team-performance/", { params: { year: this.year } });
            this.team = res.data.team;
            this.histogram = res.data.histogram;
            this.taskStatusCounts = res.data.task_status_counts;
            this.$nextTick(() => { this.renderHistogram(); this.renderTaskStatus(); });
        },
        renderHistogram() {
            const ctx = document.getElementById("histogram-chart");
            if (!ctx) return;
            new Chart(ctx, {
                type: "bar",
                data: {
                    labels: this.histogram.map(h => `${window.PersianUtils.toFaNumber(h.range_low, 0)}-${window.PersianUtils.toFaNumber(h.range_high, 0)}`),
                    datasets: [{ label: "تعداد کارمندان", data: this.histogram.map(h => h.count), backgroundColor: "#0d6efd" }],
                },
                options: { responsive: true, plugins: { legend: { display: false } } },
            });
        },
        renderTaskStatus() {
            const ctx = document.getElementById("task-status-chart");
            if (!ctx) return;
            const labelMap = { PENDING: "در انتظار", IN_PROGRESS: "در حال انجام", COMPLETED: "تکمیل‌شده", REJECTED: "رد شده" };
            new Chart(ctx, {
                type: "doughnut",
                data: {
                    labels: this.taskStatusCounts.map(t => labelMap[t.status] || t.status),
                    datasets: [{ data: this.taskStatusCounts.map(t => t.count), backgroundColor: ["#6c757d", "#0d6efd", "#198754", "#dc3545"] }],
                },
                options: { responsive: true },
            });
        },
    },
};
