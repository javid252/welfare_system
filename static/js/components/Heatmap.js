window.Components = window.Components || {};

window.Components.Heatmap = {
    template: `
    <div>
        <h4 class="mb-4">نقشه حرارتی مقایسه‌ای استانی/شهرستانی — سال {{ year }}</h4>
        <div class="table-responsive">
            <table class="table table-bordered text-center align-middle">
                <thead><tr><th>استان</th><th>شهرستان</th><th>تعداد کارمند</th><th>میانگین واحد کار تعدیل‌شده</th></tr></thead>
                <tbody>
                    <tr v-for="row in heatmap" :key="row.province_code + row.region_code">
                        <td>{{ row.province_code || '—' }}</td>
                        <td>{{ row.region_code }}</td>
                        <td>{{ row.employee_count | faNum(0) }}</td>
                        <td :style="cellStyle(row.average_adjusted_swu)">{{ row.average_adjusted_swu | faNum(2) }}</td>
                    </tr>
                    <tr v-if="!heatmap.length"><td colspan="4" class="text-center text-muted py-3">داده‌ای موجود نیست.</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    `,
    data() {
        return { year: new Date().getFullYear(), heatmap: [] };
    },
    mounted() { this.load(); },
    methods: {
        async load() {
            const res = await api.get("dashboard/province-heatmap/", { params: { year: this.year } });
            this.heatmap = res.data.heatmap;
        },
        cellStyle(value) {
            const max = Math.max(1, ...this.heatmap.map(r => r.average_adjusted_swu));
            const intensity = Math.round((value / max) * 200);
            return {
                backgroundColor: `rgba(13, 110, 253, ${0.1 + (value / max) * 0.6})`,
                fontWeight: "bold",
            };
        },
    },
};
