<template>
  <div v-if="sources?.length" class="source-panel">
    <button type="button" class="source-panel-head" @click="panelOpen = !panelOpen">
      <span class="source-panel-title">
        引用来源（{{ sources.length }} 个相关片段）
      </span>
      <el-icon class="source-panel-arrow" :class="{ open: panelOpen }">
        <ArrowRight />
      </el-icon>
    </button>

    <div v-show="panelOpen" class="source-panel-body">
      <div
        v-for="(s, idx) in sources"
        :key="`${s.chunk_id || s.filename || 's'}-${idx}`"
        class="source-item"
        :class="{ open: expanded[idx] }"
      >
        <button type="button" class="source-item-head" @click="toggle(idx)">
          <el-icon class="source-item-chevron" :class="{ open: expanded[idx] }">
            <ArrowRight />
          </el-icon>
          <el-icon class="source-item-file"><Document /></el-icon>
          <span class="source-item-name" :title="displayName(s, idx)">
            来源{{ idx + 1 }}: {{ displayName(s, idx) }}
          </span>
          <span v-if="s.score != null" class="source-item-score">
            {{ formatScore(s.score) }}
          </span>
        </button>
        <div v-show="expanded[idx]" class="source-item-content">
          {{ s.content || '（无片段正文）' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'

const props = defineProps({
  sources: { type: Array, default: () => [] },
})

// 默认展开整块引用区；每条片段默认收起，点开看正文
const panelOpen = ref(true)
const expanded = reactive({})

watch(
  () => props.sources,
  (list) => {
    const n = (list || []).length
    for (let i = 0; i < n; i += 1) {
      if (expanded[i] === undefined) expanded[i] = false
    }
  },
  { immediate: true, deep: true },
)

function toggle(idx) {
  expanded[idx] = !expanded[idx]
}

function displayName(source, idx) {
  const name = (source?.filename || '').trim()
  return name || `知识片段 ${idx + 1}`
}

function formatScore(score) {
  const pct = Number(score) * 100
  if (Number.isNaN(pct)) return ''
  return `${pct.toFixed(1)}%`
}
</script>
