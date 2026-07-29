window.Components = window.Components || {};

window.Components.AuditQueue = {
    template: `
    <div>
        <h4 class="mb-4">صف ممیزی کیفیت</h4>
        <p class="text-muted">۵٪ از فعالیت‌های تایید شده هر کارمند به‌صورت تصادفی برای ممیزی کیفیت انتخاب می‌شوند.</p>
        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead>
                    <tr><th>کارمند</th><th>خدمت</th><th>تاریخ</th><th>امتیاز کیفیت (۰ تا ۱۰۰)</th><th></th></tr>
                </thead>
                <tbody>
                    <tr v-for="a in items" :key="a.id">
                        <td>{{ a.employee_detail.full_name }} ({{ a.employee_detail.employee_code }})</td>
                        <td>{{ a.service_detail.name }}</td>
                        <td>{{ a.date_performed | faDate }}</td>
                        <td>
                            <input type="number" min="0" max="100" class="form-control form-control-sm"
                                   style="width:100px" v-model.number="a._score">
                        </td>
                        <td><button class="btn btn-sm btn-primary" @click="submit(a)">ثبت امتیاز</button></td>
                    </tr>
                    <tr v-if="!items.length"><td colspan="5" class="text-center text-muted py-3">موردی برای ممیزی وجود ندارد.</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    `,
    data() {
        return { items: [] };
    },
    mounted() { this.load(); },
    methods: {
        async load() {
            const res = await api.get("activities/audit-queue/");
            const list = res.data.results || res.data;
            this.items = list.map(a => ({ ...a, _score: 90 }));
        },
        async submit(a) {
            await api.post(`activities/${a.id}/submit-audit/`, { audit_score: a._score });
            await this.load();
        },
    },
};
