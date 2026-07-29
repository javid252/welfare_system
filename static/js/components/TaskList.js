window.Components = window.Components || {};

window.Components.TaskList = {
    template: `
    <div>
        <h4 class="mb-4">وظایف محول‌شده به من</h4>
        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead>
                    <tr><th>خدمت</th><th>شرح</th><th>اولویت</th><th>مهلت</th><th>وضعیت</th><th></th></tr>
                </thead>
                <tbody>
                    <tr v-for="t in tasks" :key="t.id">
                        <td>{{ t.service_detail.name }}</td>
                        <td>{{ t.description }}</td>
                        <td><span class="badge" :class="priorityBadge(t.priority)">{{ priorityLabel(t.priority) }}</span></td>
                        <td>{{ t.deadline | faDate }}</td>
                        <td><span class="badge" :class="statusBadge(t.status)">{{ statusLabel(t.status) }}</span></td>
                        <td>
                            <select class="form-select form-select-sm" style="width:auto"
                                    :value="t.status" @change="updateStatus(t, $event.target.value)">
                                <option value="PENDING">در انتظار</option>
                                <option value="IN_PROGRESS">در حال انجام</option>
                                <option value="COMPLETED">تکمیل‌شده</option>
                                <option value="REJECTED">رد شده</option>
                            </select>
                        </td>
                    </tr>
                    <tr v-if="!tasks.length"><td colspan="6" class="text-center text-muted py-3">وظیفه‌ای یافت نشد.</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    `,
    data() {
        return { tasks: [] };
    },
    mounted() {
        this.load();
    },
    methods: {
        priorityLabel(p) { return { LOW: "کم", MEDIUM: "متوسط", HIGH: "بالا" }[p] || p; },
        priorityBadge(p) { return { LOW: "bg-secondary", MEDIUM: "bg-info", HIGH: "bg-danger" }[p] || "bg-secondary"; },
        statusLabel(s) { return { PENDING: "در انتظار", IN_PROGRESS: "در حال انجام", COMPLETED: "تکمیل‌شده", REJECTED: "رد شده" }[s] || s; },
        statusBadge(s) { return { PENDING: "bg-secondary", IN_PROGRESS: "bg-primary", COMPLETED: "bg-success", REJECTED: "bg-danger" }[s] || "bg-secondary"; },
        async load() {
            const res = await api.get("tasks/", { params: { assigned_to: window.CURRENT_USER.id } });
            this.tasks = res.data.results || res.data;
        },
        async updateStatus(task, status) {
            await api.patch(`tasks/${task.id}/`, { status });
            await this.load();
        },
    },
};
