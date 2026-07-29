window.Components = window.Components || {};

window.Components.Approvals = {
    template: `
    <div>
        <h4 class="mb-4">تایید ضرایب پیچیدگی درخواستی</h4>
        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead>
                    <tr><th>کارمند</th><th>خدمت</th><th>تاریخ</th><th>ضریب درخواستی</th><th>اقدام</th></tr>
                </thead>
                <tbody>
                    <tr v-for="a in items" :key="a.id">
                        <td>{{ a.employee_detail.full_name }} ({{ a.employee_detail.employee_code }})</td>
                        <td>{{ a.service_detail.name }}</td>
                        <td>{{ a.date_performed | faDate }}</td>
                        <td>
                            <input type="number" step="0.1" min="1" max="3" class="form-control form-control-sm"
                                   style="width:90px" v-model.number="a._coefficient">
                        </td>
                        <td>
                            <button class="btn btn-sm btn-success me-1" @click="act(a, true)">تایید</button>
                            <button class="btn btn-sm btn-outline-danger" @click="act(a, false)">رد</button>
                        </td>
                    </tr>
                    <tr v-if="!items.length"><td colspan="5" class="text-center text-muted py-3">درخواستی در انتظار تایید نیست.</td></tr>
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
            const res = await api.get("activities/pending-complexity/");
            const list = res.data.results || res.data;
            this.items = list.map(a => ({ ...a, _coefficient: a.complexity_coefficient }));
        },
        async act(a, approve) {
            await api.post(`activities/${a.id}/approve-complexity/`, {
                approve, complexity_coefficient: a._coefficient,
            });
            await this.load();
        },
    },
};
