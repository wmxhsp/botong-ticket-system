<template>
  <div class="card p-3 p-md-4 mb-2">
    <h5 class="mb-3 d-flex align-items-center gap-2">
      <i class="bi bi-box-seam me-2"></i>物料清单
      <button class="btn btn-sm btn-outline-primary ms-auto" @click="$emit('add-material')">
        <i class="bi bi-plus-lg"></i> 添加物料
      </button>
    </h5>
    <div v-if="!materials || materials.length === 0" class="text-muted small py-4 text-center">
      <i class="bi bi-box-seam me-1"></i>暂无物料
    </div>
    <div v-else class="table-responsive">
      <table class="table table-sm">
        <thead>
          <tr>
            <th>商品名称</th>
            <th class="text-center">数量</th>
            <th class="text-center d-none d-md-table-cell">单价</th>
            <th class="text-center">小计</th>
            <th class="text-center d-none d-sm-table-cell">库存</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in materials" :key="m.id">
            <td>{{ m.name || m.product_name }}</td>
            <td class="text-center">
              <input type="number" :value="m.quantity" @change="$emit('update-qty', m.id, $event)" class="form-control form-control-sm" style="width:70px;display:inline-block" min="1">
            </td>
            <td class="text-center d-none d-md-table-cell">¥{{ formatMoney(m.unit_price || 0) }}</td>
            <td class="text-center">¥{{ formatMoney((m.quantity || 1) * (m.unit_price || 0)) }}</td>
            <td class="text-center d-none d-sm-table-cell">
              <span :class="(m.stock || 0) > 0 ? 'text-success' : 'text-danger'">
                {{ m.stock || 0 }}
              </span>
            </td>
            <td class="text-right">
              <button class="btn btn-sm btn-outline-danger" @click="$emit('delete-material', m.id)">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
defineProps({
  materials: { type: Array, default: () => [] },
})
defineEmits(['add-material', 'delete-material', 'update-qty'])

function formatMoney(val) { return parseFloat(val || 0).toFixed(2) }
</script>
