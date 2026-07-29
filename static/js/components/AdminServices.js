window.Components = window.Components || {};

window.Components.AdminServices = {
    template: `
    <div>
        <h4 class="mb-4">مدیریت کاتالوگ خدمات</h4>

        <div class="card mb-4">
            <div class="card-header fw-bold">{{ editing ? 'ویرایش خدمت' : 'افزودن خدمت جدید' }}</div>
            <div class="card-body">
                <form @submit.prevent="save" class="row g-3">
                    <div class="col-md-3">
                        <label class="form-label">کد خدمت</label>
                        <input class="form-control" v-model="form.service_code" required>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label">نام خدمت</label>
                        <input class="form-control" v-model="form.name" required>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">واحد کار پایه</label>
                        <input type="number" step="0.1" min="0" class="form-control" v-model.number="form.base_swu" required>
                    </div>
                    <div class="col-md-2 d-flex align-items-end">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" v-model="form.is_active" id="isActive">
                            <label class="form-check-label" for="isActive">فعال</label>
                        </div>
                    </div>
                    <div class="col-12">
                        <label class="form-label">شرح</label>
                        <textarea class="form-control" v-model="form.description" rows="2"></textarea>
                    </div>
                    <div class="col-12">
                        <button class="btn btn-primary">{{ editing ? 'ذخیره تغییرات' : 'افزودن' }}</button>
                        <button v-if="editing" type="button" class="btn btn-outline-secondary ms-2" @click="resetForm">انصراف</button>
                    </div>
                </form>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead><tr><th>کد</th><th>نام</th><th>واحد پایه</th><th>وضعیت</th><th></th></tr></thead>
                <tbody>
                    <tr v-for="s in services" :key="s.id">
                        <td>{{ s.service_code }}</td>
                        <td>{{ s.name }}</td>
                        <td>{{ s.base_swu | faNum(2) }}</td>
                        <td><span class="badge" :class="s.is_active ? 'bg-success' : 'bg-secondary'">{{ s.is_active ? 'فعال' : 'غیرفعال' }}</span></td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary me-1" @click="edit(s)">ویرایش</button>
                            <button v-if="s.is_deletable" class="btn btn-sm btn-outline-danger" @click="remove(s)">حذف</button>
                            <button v-else class="btn btn-sm" :class="s.is_active ? 'btn-outline-secondary' : 'btn-outline-success'"
                                    @click="toggleActive(s)" :title="'این خدمت در فعالیت‌ها یا وظایف قبلی استفاده شده و قابل حذف نیست'">
                                {{ s.is_active ? 'غیرفعال کردن' : 'فعال کردن' }}
                            </button>
                        </td>
                    </tr>
                    <tr v-if="!services.length"><td colspan="5" class="text-center text-muted py-3">خدمتی ثبت نشده است.</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    `,
    data() {
        return {
            services: [],
            editing: null,
            form: { service_code: "", name: "", description: "", base_swu: 1, is_active: true },
        };
    },
    mounted() { this.load(); },
    methods: {
        async load() {
            const res = await api.get("services/");
            this.services = res.data.results || res.data;
        },
        edit(s) {
            this.editing = s.id;
            this.form = { ...s };
        },
        resetForm() {
            this.editing = null;
            this.form = { service_code: "", name: "", description: "", base_swu: 1, is_active: true };
        },
        async save() {
            if (this.editing) {
                await api.put(`services/${this.editing}/`, this.form);
            } else {
                await api.post("services/", this.form);
            }
            this.resetForm();
            await this.load();
        },
        async remove(s) {
            if (!confirm(`حذف خدمت «${s.name}»؟`)) return;
            try {
                await api.delete(`services/${s.id}/`);
                await this.load();
            } catch (e) {
                // Safety net for a race condition (e.g. someone logged an
                // activity against this service between page-load and click).
                const data = e.response && e.response.data;
                if (data && data.code === "protected") {
                    alert(data.detail);
                    await this.load();
                } else {
                    alert("حذف خدمت با خطا مواجه شد.");
                }
            }
        },
        async toggleActive(s) {
            await api.patch(`services/${s.id}/`, { is_active: !s.is_active });
            await this.load();
        },
    },
};
