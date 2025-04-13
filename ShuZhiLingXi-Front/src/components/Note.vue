<template>
  <main-layouts>
    <div class="dashboard-container">
      <!-- 左侧边栏 -->
      <div class="side-widgets">
        <!-- 笔记统计卡片 -->
        <div class="widget-card stats-card">
          <div class="stats-header">
            <h3>笔记概览</h3>
          </div>
          <div class="statistics-grid">
            <div class="stat-item total">
              <div class="stat-value">{{ noteStore.statistics.notes_count }}</div>
              <div class="stat-label">总笔记</div>
            </div>
            <div class="stat-item clear">
              <div class="stat-value">{{ noteStore.statistics.clear_notes_count }}</div>
              <div class="stat-label">已理解</div>
            </div>
            <div class="stat-item vague">
              <div class="stat-value">{{ noteStore.statistics.vague_notes_count }}</div>
              <div class="stat-label">待复习</div>
            </div>
            <div class="stat-item unclear">
              <div class="stat-value">{{ noteStore.statistics.unclear_notes_count }}</div>
              <div class="stat-label">不理解</div>
            </div>
          </div>
        </div>

        <!-- 章节列表卡片 -->
        <div class="widget-card chapters-card">
          <div class="widget-header">
            <h3>章节列表</h3>
            <el-button
                class="create-chapter-btn"
                @click="showCreateChapterDialog">
              <el-icon><Plus /></el-icon>
              新建章节
            </el-button>
          </div>

          <!-- 科目筛选 -->
          <div class="subject-filter">
            <el-radio-group v-model="currentSubject" size="small">
              <el-radio-button label="all">
                <el-icon><Grid /></el-icon>
                全部
              </el-radio-button>
              <el-radio-button
                  v-for="category in noteStore.subjectCategories"
                  :key="category.value"
                  :label="category.value">
                <el-icon>
                  <component :is="getSubjectIcon(category.value)" />
                </el-icon>
                {{ category.label }}
              </el-radio-button>
            </el-radio-group>
          </div>

          <!-- 章节列表 -->
          <div class="chapters-list">
            <el-scrollbar>
              <el-collapse v-model="activeChapters">
                <el-collapse-item
                    v-for="chapter in filteredChapters"
                    :key="chapter.chapter_id"
                    :name="chapter.chapter_id">
                  <template #title>
                    <div class="chapter-title">
                      <div class="chapter-title-left">
                        <el-tag
                            size="small"
                            :type="getSubjectTagType(chapter.category)"
                            :effect="getTagEffect(chapter.category)"
                            class="subject-tag">
                          <el-icon class="subject-icon">
                            <component :is="getSubjectIcon(chapter.category)" />
                          </el-icon>
                          {{ chapter.categoryName || noteStore.getCategoryName(chapter.category) }}
                        </el-tag>
                        <span class="chapter-name">{{ chapter.name }}</span>
                      </div>
                    </div>
                  </template>
                  <div class="chapter-content">
                    <div class="chapter-info">
                      <el-tag
                          size="small"
                          type="info"
                          effect="plain"
                          class="note-count">
                        {{ chapter.note_count || 0 }} 笔记
                      </el-tag>
                    </div>
                    <div class="chapter-actions">
                      <el-tooltip
                          content="查看笔记"
                          placement="top"
                          :show-after="500">
                        <el-button
                            type="primary"
                            link
                            class="action-button"
                            @click.stop="handleChapterSelect(chapter)">
                          <el-icon><View /></el-icon>
                          查看
                        </el-button>
                      </el-tooltip>

                      <el-tooltip
                          content="编辑章节"
                          placement="top"
                          :show-after="500">
                        <el-button
                            type="warning"
                            link
                            class="action-button"
                            @click.stop="editChapter(chapter)">
                          <el-icon><Edit /></el-icon>
                          编辑
                        </el-button>
                      </el-tooltip>

                      <el-popconfirm
                          title="确定要删除这个章节吗？"
                          confirm-button-text="确定"
                          cancel-button-text="取消"
                          @confirm="deleteChapter(chapter.chapter_id)">
                        <template #reference>
                          <el-button
                              type="danger"
                              link
                              class="action-button"
                              @click.stop>
                            <el-icon><Delete /></el-icon>
                            删除
                          </el-button>
                        </template>
                      </el-popconfirm>
                    </div>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </el-scrollbar>
          </div>
        </div>
      </div>

      <!-- 右侧笔记内容区 -->
      <div class="notes-content">
        <div class="header">
          <h2>{{ currentChapter?.name || '请选择章节' }}</h2>
          <div class="header-actions">
            <el-button
                type="primary"
                class="kg-button"
                @click="showKnowledgeGraphDrawer"
                :disabled="!currentChapter">
              <el-icon><Connection /></el-icon>
              知识图谱
            </el-button>
            <el-button
                type="primary"
                class="summary-button"
                @click="showSummaryDrawer"
                :disabled="!currentChapter">
              <el-icon><Document /></el-icon>
              查看总结
            </el-button>
            <el-button
                type="primary"
                class="custom-add-button"
                @click="showCreateNoteDialog"
                :disabled="!currentChapter">
              <el-icon><Plus /></el-icon>
              新建笔记
            </el-button>
          </div>
        </div>

        <!-- 使用 el-scrollbar 包裹笔记列表 -->
        <el-scrollbar class="notes-scrollbar">
          <div class="notes-list">
            <el-tabs v-model="activeCategory" type="card" class="category-tabs">
              <el-tab-pane label="全部笔记" name="all">
                <div class="notes-grid">
                  <el-card v-for="note in filteredNotes"
                           :key="note.note_id"
                           class="note-card"
                           :class="note.comprehension_level">
                    <template #header>
                      <div class="note-header">
                        <div class="note-info">
                          <span class="note-date">{{ formatDate(note.created_at) }}</span>
                          <div class="note-level">
                            <el-tag :type="getLevelType(note.comprehension_level)">
                              {{ note.comprehension_level }}
                            </el-tag>
                          </div>
                        </div>
                        <div class="note-actions">
                          <el-button-group>
                            <el-button
                                text
                                size="small"
                                @click="editNote(note)">
                              <el-icon><Edit /></el-icon>
                              编辑
                            </el-button>
                            <el-button
                                text
                                type="danger"
                                size="small"
                                @click="deleteNote(note.note_id)">
                              <el-icon><Delete /></el-icon>
                              删除
                            </el-button>
                          </el-button-group>
                        </div>
                      </div>
                    </template>
                    <div class="note-content">
                      <el-image
                          v-if="note.is_image"
                          :src="note.image_url"
                          :preview-src-list="[note.image_url]"
                          class="note-image"
                          fit="contain"
                      />
                      <audio v-if="note.is_audio" :src="note.audio_url" controls class="note-audio" />
                      <div v-if="note.audio_describe" class="audio-description">
                        {{ note.audio_describe }}
                      </div>
                      <div class="note-text" v-html="renderContent(note.words)"></div>
                    </div>
                  </el-card>
                </div>
              </el-tab-pane>
              <el-tab-pane v-for="level in comprehensionLevels"
                           :key="level"
                           :label="level"
                           :name="level">
                <div class="notes-grid">
                  <el-card v-for="note in getNotesByLevel(level)"
                           :key="note.note_id"
                           class="note-card"
                           :class="note.comprehension_level">
                    <template #header>
                      <div class="note-header">
                        <div class="note-info">
                          <span class="note-date">{{ formatDate(note.created_at) }}</span>
                          <div class="note-level">
                            <el-tag :type="getLevelType(note.comprehension_level)">
                              {{ note.comprehension_level }}
                            </el-tag>
                          </div>
                        </div>
                        <div class="note-actions">
                          <el-button-group>
                            <el-button
                                text
                                size="small"
                                @click="editNote(note)">
                              <el-icon><Edit /></el-icon>
                              编辑
                            </el-button>
                            <el-button
                                text
                                type="danger"
                                size="small"
                                @click="deleteNote(note.note_id)">
                              <el-icon><Delete /></el-icon>
                              删除
                            </el-button>
                          </el-button-group>
                        </div>
                      </div>
                    </template>
                    <div class="note-content">
                      <el-image
                          v-if="note.is_image"
                          :src="note.image_url"
                          :preview-src-list="[note.image_url]"
                          class="note-image"
                          fit="contain"
                      />
                      <audio v-if="note.is_audio" :src="note.audio_url" controls class="note-audio" />
                      <div v-if="note.audio_describe" class="audio-description">
                        {{ note.audio_describe }}
                      </div>
                      <div class="note-text" v-html="renderContent(note.words)"></div>
                    </div>
                  </el-card>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-scrollbar>

        <!-- 创建章节对话框 -->
        <el-dialog
            v-model="chapterDialogVisible"
            :title="editingChapter ? '编辑章节' : '新建章节'"
            width="500px"
            custom-class="custom-dialog">
          <el-form :model="chapterForm" label-position="top">
            <el-form-item label="章节名称">
              <el-input v-model="chapterForm.name" placeholder="请输入章节名称" />
            </el-form-item>
            <el-form-item label="分类">
              <el-select
                  v-model="chapterForm.category"
                  :options="formattedCategories"
                  placeholder="请选择分类"
                  clearable
                  filterable
                  style="width: 100%"
              >
                <el-option
                    v-for="category in formattedCategories"
                    :key="category.value"
                    :label="category.label"
                    :value="category.value"
                />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <div class="dialog-footer">
              <el-button @click="chapterDialogVisible = false">取消</el-button>
              <el-button
                  class="custom-confirm-btn"
                  @click="handleChapterSubmit">
                {{ editingChapter ? '更新' : '创建' }}
              </el-button>
            </div>
          </template>
        </el-dialog>

        <!-- 创建/编辑笔记对话框 -->
        <el-dialog
            v-model="noteDialogVisible"
            :title="editingNote ? '编辑笔记' : '新建笔记'"
            width="500px"
            custom-class="custom-dialog">
          <el-form :model="noteForm" label-position="top">
            <el-form-item label="图片">
              <el-upload
                  class="image-upload"
                  action="#"
                  :auto-upload="false"
                  :on-change="handleImageChange"
                  accept="image/*"
              >
                <el-button class="custom-upload-btn">
                  <el-icon><Plus /></el-icon>
                  选择图片
                </el-button>
              </el-upload>
            </el-form-item>
            <el-form-item label="音频">
              <el-upload
                  class="audio-upload"
                  action="#"
                  :auto-upload="false"
                  :on-change="handleAudioChange"
                  accept="audio/*"
              >
                <el-button class="custom-upload-btn">
                  <el-icon><Plus /></el-icon>
                  选择音频
                </el-button>
              </el-upload>
            </el-form-item>
            <el-form-item label="笔记内容">
              <el-input
                  v-model="noteForm.words"
                  type="textarea"
                  :rows="4"
                  placeholder="请输入笔记内容"
              />
            </el-form-item>
            <el-form-item label="理解程度">
              <el-select
                  v-model="noteForm.comprehension_level"
                  style="width: 100%"
                  placeholder="请选择理解程度">
                <el-option
                    v-for="level in comprehensionLevels"
                    :key="level"
                    :label="level"
                    :value="level">
                  <el-tag :type="getLevelType(level)" size="small">
                    {{ level }}
                  </el-tag>
                </el-option>
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <div class="dialog-footer">
              <el-button @click="noteDialogVisible = false">取消</el-button>
              <el-button
                  class="custom-confirm-btn"
                  @click="handleNoteSubmit">
                {{ editingNote ? '更新' : '创建' }}
              </el-button>
            </div>
          </template>
        </el-dialog>
      </div>
    </div>

    <!-- 笔记总结抽屉 -->
    <el-drawer
        v-model="drawerVisible"
        title="笔记总结"
        size="35%"
        :destroy-on-close="false">
      <div class="summary-container">
        <!-- 总结内容区域 -->
        <template v-if="!noteStore.isLoadingSummary || noteStore.summary">
          <div class="summary-content markdown-content" v-html="markedSummary"></div>
        </template>

        <!-- 加载状态显示 -->
        <div v-if="noteStore.isLoadingSummary && !noteStore.summary" class="loading-overlay">
          <el-icon class="loading-icon" :size="24">
            <Loading />
          </el-icon>
          <span class="loading-text">正在生成总结...</span>
        </div>

        <!-- 空状态显示 -->
        <div v-else-if="!noteStore.summary" class="empty-summary">
          <p>暂无总结内容，点击下方按钮生成</p>
        </div>

        <!-- 重新生成按钮 -->
        <el-button
            class="regenerate-button"
            :disabled="noteStore.isLoadingSummary"
            :class="{ 'is-loading': noteStore.isLoadingSummary }"
            @click="generateNewSummary">
          <template #icon>
            <el-icon v-if="noteStore.isLoadingSummary"><Loading /></el-icon>
            <el-icon v-else><Refresh /></el-icon>
          </template>
          {{ noteStore.isLoadingSummary ? '正在生成...' : '重新生成' }}
        </el-button>
      </div>
    </el-drawer>
    <!-- 知识图谱抽屉 -->
    <el-drawer
        v-model="kgDrawerVisible"
        title="知识图谱"
        size="35%"
        :destroy-on-close="false">
      <div class="kg-container">
        <div class="kg-actions">
          <el-button
              class="regenerate-button"
              :disabled="kgLoading"
              @click="handleRegenerateGraph">
            <el-icon v-if="kgLoading"><Loading /></el-icon>
            <el-icon v-else><Refresh /></el-icon>
            {{ kgLoading ? '正在生成...' : '重新生成图谱' }}
          </el-button>
        </div>

        <div v-if="kgLoading" class="loading-overlay">
          <el-icon class="loading-icon" :size="24">
            <Loading />
          </el-icon>
          <span class="loading-text">正在加载知识图谱...</span>
        </div>

        <div v-if="kgError" class="error-message">
          {{ kgError }}
        </div>

        <div v-if="knowledgeGraph" class="kg-content">
          <div class="kg-graph" ref="kgContainer" style="width: 100%; height: 100%"></div>
        </div>
      </div>
    </el-drawer>
  </main-layouts>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick, onUnmounted } from 'vue';
import { useNoteStore } from '../stores/note';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import MainLayouts from "../layouts/MainLayouts.vue";
import { Plus, Grid, View, Edit, Delete, Document, Loading, Refresh,Connection } from '@element-plus/icons-vue';
import { marked } from 'marked'
import { useUserStore } from '../stores/user';
import * as d3 from 'd3'
import katex from 'katex'
import 'katex/dist/katex.min.css'

const noteStore = useNoteStore();
const route = useRoute();
const router = useRouter();

// 状态变量
const chapterDialogVisible = ref(false);
const noteDialogVisible = ref(false);
const editingChapter = ref(null);
const editingNote = ref(null);
const userInfo = ref(null);

const kgDrawerVisible = ref(false)
const knowledgeGraph = ref(null)
const kgLoading = ref(false)
const kgError = ref('')
const kgContainer = ref(null)

const chapterForm = ref({
  name: '',
  category: null
});

const noteForm = ref({
  chapter_id: null,
  image: null,
  is_image: false,
  image_describe: '',
  audio: null,
  is_audio: false,
  audio_describe: '',
  words: '',
  comprehension_level: '理解'
});

// 计算属性
const currentChapter = computed(() => noteStore.currentChapter);
const notes = computed(() => noteStore.notes);
const categories = computed(() => noteStore.categories || []);

// 格式化分类数据为树形结构
const formattedCategories = computed(() => {
  return noteStore.formatCategoryTree(noteStore.categories);
});

// 添加新的响应式变量
const activeChapters = ref([]);
const activeCategory = ref('all');
const comprehensionLevels = ref(['理解', '模糊', '不理解']);

// 根据理解程度过滤笔记
const filteredNotes = computed(() => {
  if (activeCategory.value === 'all') {
    return notes.value;
  }
  return notes.value.filter(note => note.comprehension_level === activeCategory.value);
});

// 获取特定理解程度的笔记
const getNotesByLevel = (level) => {
  return notes.value.filter(note => note.comprehension_level === level);
};

// 获取标签类型
const getLevelType = (level) => {
  switch (level) {
    case '理解':
      return 'success';
    case '模糊':
      return 'warning';
    case '不理解':
      return 'danger';
    default:
      return 'info';
  }
};

// 添加科目相关的响应式变量和方法
const currentSubject = ref('all');

// 修改过滤章节列表的计算属性
const filteredChapters = computed(() => {
  if (currentSubject.value === 'all') {
    return noteStore.chapters;
  }
  // 修改筛选逻辑，使用 category 而不是 category_id
  return noteStore.chapters.filter(chapter => Number(chapter.category) === currentSubject.value);
});

// 修改获取科目图标的方法
const getSubjectIcon = (categoryId) => {
  if (!categoryId) return 'Grid';
  const category = noteStore.subjectCategories.find(c => c.value === Number(categoryId));
  if (!category) return 'Grid';

  switch (category.type) {
    case 'chinese':
      return 'Reading';
    case 'math':
      return 'Operation';
    case 'english':
      return 'ChatDotRound';
    default:
      return 'Grid';
  }
};

// 修改获取科目标签类型的方法
const getSubjectTagType = (categoryId) => {
  if (!categoryId) return 'info';
  const category = noteStore.subjectCategories.find(c => c.value === Number(categoryId));
  if (!category) return 'info';

  switch (category.type) {
    case 'chinese':
      return 'success';
    case 'math':
      return 'warning';
    case 'english':
      return 'info';
    default:
      return 'info';
  }
};

// 修改获取标签效果的方法
const getTagEffect = (categoryId) => {
  if (!categoryId) return 'plain';
  const category = noteStore.subjectCategories.find(c => c.value === Number(categoryId));
  return category ? 'light' : 'plain';
};

// 添加计算属性来处理分类显示
const getChapterCategoryName = (chapter) => {
  return chapter.categoryName || noteStore.getCategoryName(chapter.category);
};

// 方法
const showCreateChapterDialog = () => {
  editingChapter.value = null;
  chapterForm.value = { name: '', category: null };
  chapterDialogVisible.value = true;
};

const handleChapterSubmit = async () => {
  try {
    if (editingChapter.value) {
      await noteStore.updateChapter(editingChapter.value.chapter_id, {
        name: chapterForm.value.name,
        category: chapterForm.value.category
      });
      ElMessage({
        message: '章节已更新',
        type: 'success',
        duration: 2000
      });
    } else {
      await noteStore.createChapter({
        name: chapterForm.value.name,
        category: chapterForm.value.category
      });
      ElMessage({
        message: '章节已创建',
        type: 'success',
        duration: 2000
      });
    }

    chapterDialogVisible.value = false;
    await noteStore.fetchChapters();
  } catch (error) {
    ElMessage.error(editingChapter.value ? '更新章节失败' : '创建章节失败');
  }
};

const showCreateNoteDialog = () => {
  editingNote.value = null;
  noteForm.value = {
    chapter_id: currentChapter.value?.chapter_id,
    image: null,
    is_image: false,
    image_describe: '',
    audio: null,
    is_audio: false,
    audio_describe: '',
    words: '',
    comprehension_level: '理解'
  };
  noteDialogVisible.value = true;
};

const handleNoteSubmit = async () => {
  try {
    if (!noteForm.value.words && !noteForm.value.image && !noteForm.value.audio) {
      ElMessage.warning('请至少添加文字、图片或音频内容');
      return;
    }

    const submitData = {
      chapter_id: currentChapter.value.chapter_id,
      image: noteForm.value.image || null,
      is_image: noteForm.value.is_image || false,
      image_describe: noteForm.value.image_describe || '',
      audio: noteForm.value.audio || null,
      is_audio: noteForm.value.is_audio || false,
      audio_describe: noteForm.value.audio_describe || '',
      words: noteForm.value.words || '',
      comprehension_level: noteForm.value.comprehension_level || '理解'
    };

    // 立即关闭弹窗并重置表单
    noteDialogVisible.value = false;
    noteForm.value = {
      chapter_id: currentChapter.value?.chapter_id,
      image: null,
      is_image: false,
      image_describe: '',
      audio: null,
      is_audio: false,
      audio_describe: '',
      words: '',
      comprehension_level: '理解'
    };

    // 显示添加中的提示
    ElMessage.info('正在添加笔记，请稍候...');

    // 异步提交数据
    if (editingNote.value) {
      await noteStore.updateNote(editingNote.value.note_id, submitData);
      ElMessage.success('笔记已更新');
    } else {
      await noteStore.createNote(submitData);
      ElMessage.success('笔记已创建');
    }

  } catch (error) {
    console.error('笔记操作失败:', error);
    ElMessage.error(editingNote.value ? '更新笔记失败' : '创建笔记失败');
  }
};

const handleImageChange = (file) => {
  // 检查文件大小（例如限制为 5MB）
  const isLt5M = file.size / 1024 / 1024 < 5;
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB!');
    return false;
  }

  // 读取图片文件为 base64
  const reader = new FileReader();
  reader.readAsDataURL(file.raw);
  reader.onload = (e) => {
    // 只保存 base64 数据部分，去掉 "data:image/jpeg;base64," 这样的前缀
    const base64Data = e.target.result.split(',')[1];
    noteForm.value.image = base64Data;
    noteForm.value.is_image = true;
  };
};

const handleAudioChange = (file) => {
  // 检查文件大小（例如限制为 10MB）
  const isLt10M = file.size / 1024 / 1024 < 10;
  if (!isLt10M) {
    ElMessage.error('音频大小不能超过 10MB!');
    return false;
  }

  // 读取音频文件为 base64
  const reader = new FileReader();
  reader.readAsDataURL(file.raw);
  reader.onload = (e) => {
    // 只保存 base64 数据部分，去掉 "data:audio/xxx;base64," 这样的前缀
    const base64Data = e.target.result.split(',')[1];
    noteForm.value.audio = base64Data;
    noteForm.value.is_audio = true;
  };
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const handleChapterSelect = (chapter) => {
  noteStore.setCurrentChapter(chapter);
  if (chapter.chapter_id) {
    noteStore.fetchNotes(chapter.chapter_id);
  }
};

const editNote = (note) => {
  editingNote.value = note;
  noteForm.value = {
    chapter_id: note.chapter_id,
    image: null,
    is_image: note.is_image || false,
    image_describe: note.image_describe || '',
    audio: null,
    is_audio: note.is_audio || false,
    audio_describe: note.audio_describe || '',
    words: note.words || '',
    comprehension_level: note.comprehension_level
  };
  noteDialogVisible.value = true;
};

const deleteNote = async (noteId) => {
  try {
    // 简化为一个简单的提示
    ElMessage({
      message: '笔记已删除',
      type: 'success',
      duration: 2000  // 2秒后自动关闭
    });

    await noteStore.deleteNote(noteId);

    // 重新获取当前章节的笔记列表
    if (currentChapter.value) {
      await noteStore.fetchNotes(currentChapter.value.chapter_id);
    }
  } catch (error) {
    ElMessage.error('删除笔记失败');
    console.error('删除笔记失败:', error);
  }
};

const editChapter = (chapter) => {
  editingChapter.value = chapter;
  chapterForm.value = {
    name: chapter.name,
    category: chapter.category
  };
  chapterDialogVisible.value = true;
};

const deleteChapter = async (chapterId) => {
  try {
    await noteStore.deleteChapter(chapterId);

    // 如果删除的是当前选中的章节，清空当前章节
    if (currentChapter.value?.chapter_id === chapterId) {
      noteStore.setCurrentChapter(null);
    }

    // 重新获取章节列表
    await noteStore.fetchChapters();

    ElMessage({
      type: 'success',
      message: '章节已删除',
      duration: 2000
    });
  } catch (error) {
    console.error('删除章节失败:', error);
    ElMessage({
      type: 'error',
      message: '删除章节失败，请稍后重试',
      duration: 2000
    });
  }
};

// 添加监听器来跟踪理解程度的变化
watch(() => noteForm.value.comprehension_level, (newValue, oldValue) => {
  console.log('理解程度变化:', oldValue, '->', newValue);
});

onMounted(async () => {
  try {
    // 先获取分类，再获取章节
    await noteStore.getCategories();
    await noteStore.fetchChapters();

    // 如果有章节，选择第一个章节
    if (noteStore.chapters.length > 0) {
      handleChapterSelect(noteStore.chapters[0]);
    }
  } catch (error) {
    console.error('初始化笔记失败:', error);
    ElMessage.error('初始化笔记失败');
  }
});

// 添加路由变化监听
watch(
    () => route.path,
    (newPath) => {
      if (newPath === '/note' && noteStore.chapters.length > 0) {
        const firstChapter = noteStore.chapters[0];
        handleChapterSelect(firstChapter);
      }
    }
);

// 添加监听器以确保章节列表更新时视图也更新
watch(
    () => noteStore.chapters,
    (newChapters) => {
      // 强制组件重新渲染
      nextTick(() => {
        if (newChapters.length > 0) {
          // 确保展开的章节仍然保持展开状态
          const expandedChapters = activeChapters.value;
          activeChapters.value = [];
          nextTick(() => {
            activeChapters.value = expandedChapters;
          });
        }
      });
    },
    { deep: true }
);

// 添加新的响应式变量
const drawerVisible = ref(false)

// 计算属性：将 Markdown 转换为 HTML
const markedSummary = computed(() => {
  return marked(noteStore.summary || '');
});

// 显示抽屉并获取或生成总结
const showSummaryDrawer = async () => {
  if (!currentChapter.value) {
    ElMessage.warning('请先选择章节')
    return
  }
  drawerVisible.value = true

  try {
    const existingSummary = await noteStore.getExistingSummary(currentChapter.value.chapter_id)
    if (existingSummary && existingSummary.summary) {
      noteStore.summary = existingSummary.summary
    } else {
      generateNewSummary()
    }
  } catch (error) {
    console.error('获取总结失败:', error)
    ElMessage.error('获取总结失败')
  }
}

// 生成新的总结
const generateNewSummary = async () => {
  if (!currentChapter.value) {
    ElMessage.warning('请先选择章节');
    return;
  }

  try {
    noteStore.isLoadingSummary = true;
    noteStore.summary = '';

    await noteStore.generateStreamingSummary(currentChapter.value.chapter_id);
    noteStore.hasExistingSummary = true;

  } catch (error) {
    console.error('生成总结失败:', error);
  } finally {
    noteStore.isLoadingSummary = false;
  }
};

const showKnowledgeGraphDrawer = async () => {
  if (!currentChapter.value) {
    ElMessage.warning('请先选择章节')
    return
  }
  kgDrawerVisible.value = true
  kgLoading.value = true
  kgError.value = ''

  try {
    const data = await noteStore.fetchKnowledgeGraph(currentChapter.value.chapter_id)
    if (data) {
      knowledgeGraph.value = data
      nextTick(() => {
        renderKnowledgeGraph()
      })
    }
  } catch (error) {
    kgError.value = '获取知识图谱失败，请稍后重试'
  } finally {
    kgLoading.value = false
  }
}

const renderKnowledgeGraph = () => {
  if (!kgContainer.value || !knowledgeGraph.value) return

  const container = kgContainer.value
  const width = container.clientWidth
  const height = container.clientHeight

  // 清空现有内容
  d3.select(container).html('')

  // 创建SVG画布
  const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .style('background', '#fff')

  // 添加缩放功能
  const zoom = d3.zoom()
      .scaleExtent([0.5, 5])
      .on('zoom', (event) => {
        svgGroup.attr('transform', event.transform)
      })

  svg.call(zoom)

  // 创建主分组
  const svgGroup = svg.append('g')

  // 添加箭头标记
  svgGroup.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .append('svg:path')
      .attr('d', 'M 0,-5 L 10,0 L 0,5')
      .attr('fill', '#6c5dd3')

  // 转换数据
  const nodes = knowledgeGraph.value.items.map(d => ({
    ...d,
    id: d.id,
    x: width/2 + Math.random()*50-25,
    y: height/2 + Math.random()*50-25
  }))

  const links = knowledgeGraph.value.relations.map(d => ({
    source: d.source,
    target: d.target,
    type: d.relation_type
  }))

  // 创建力导向图
  const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links)
          .id(d => d.id)
          .distance(150))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width/2, height/2))
      .force('collide', d3.forceCollide(30))

  // 绘制连线
  const link = svgGroup.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('class', 'link')
      .attr('stroke', '#dcdfe6')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 1.5)
      .attr('marker-end', 'url(#arrowhead)')

  // 添加关系类型标签
  const linkLabels = svgGroup.append('g')
      .selectAll('text')
      .data(links)
      .join('text')
      .attr('class', 'link-label')
      .text(d => d.type)
      .attr('font-size', 10)
      .attr('fill', '#606266')
      .attr('text-anchor', 'middle')
      .attr('dy', -5)

  // 绘制节点
  const node = svgGroup.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('class', 'node')
      .attr('r', 12)
      .attr('fill', '#6c5dd3')
      .attr('stroke', '#8674ff')
      .attr('stroke-width', 2)
      .call(d3.drag()
          .on('start', dragstarted)
          .on('drag', dragged)
          .on('end', dragended))

  // 节点文字
  const labels = svgGroup.append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .attr('class', 'node-label')
      .text(d => d.name)
      .attr('font-size', 12)
      .attr('dx', 15)
      .attr('dy', 4)

  // 添加缩放控制
  const zoomControls = svg.append('g')
      .attr('class', 'zoom-controls')

  zoomControls.append('g')
      .attr('class', 'zoom-button')
      .on('click', () => {
        svg.transition()
            .duration(750)
            .call(zoom.scaleTo, 1.2)
      })
      .append('text')
      .attr('x', 16)
      .attr('y', 20)
      .text('+')

  zoomControls.append('g')
      .attr('class', 'zoom-button')
      .on('click', () => {
        svg.transition()
            .duration(750)
            .call(zoom.scaleTo, 0.8)
      })
      .append('text')
      .attr('x', 16)
      .attr('y', 20)
      .text('-')

  // 添加搜索框
  const searchBox = svg.append('g')
      .attr('class', 'kg-search')

  searchBox.append('rect')
      .attr('width', 240)
      .attr('height', 32)
      .attr('rx', 8)
      .attr('fill', 'white')

  searchBox.append('text')
      .attr('x', 10)
      .attr('y', 20)
      .text('🔍')

  searchBox.append('text')
      .attr('x', 30)
      .attr('y', 20)
      .text('搜索节点...')
      .attr('fill', '#909399')

  // 添加图例
  const legend = svg.append('g')
      .attr('class', 'kg-legend')

  legend.append('rect')
      .attr('width', 120)
      .attr('height', 80)
      .attr('rx', 8)
      .attr('fill', 'white')

  const legendItems = [
    { color: '#6c5dd3', label: '知识点' },
    { color: '#dcdfe6', label: '关系' }
  ]

  legend.selectAll('.kg-legend-item')
      .data(legendItems)
      .join('g')
      .attr('class', 'kg-legend-item')
      .attr('transform', (d, i) => `translate(10, ${20 + i * 25})`)
      .each(function(d) {
        d3.select(this)
            .append('circle')
            .attr('class', 'kg-legend-color')
            .attr('fill', d.color)
            .attr('r', 6)

        d3.select(this)
            .append('text')
            .attr('class', 'kg-legend-label')
            .attr('x', 20)
            .attr('y', 4)
            .text(d.label)
      })

  // 更新位置函数
  simulation.on('tick', () => {
    link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)

    linkLabels
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2)

    node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y)

    labels
        .attr('x', d => d.x)
        .attr('y', d => d.y)
  })

  // 拖拽功能
  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    event.subject.fx = event.subject.x
    event.subject.fy = event.subject.y
  }

  function dragged(event) {
    event.subject.fx = event.x
    event.subject.fy = event.y
  }

  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0)
    event.subject.fx = null
    event.subject.fy = null
  }
}

const handleRegenerateGraph = async () => {
  if (!currentChapter.value) return

  kgLoading.value = true
  kgError.value = ''

  try {
    ElMessage({
      message: '正在重新生成知识图谱，这可能需要一些时间...',
      type: 'info',
      duration: 0,
      showClose: true
    })

    await noteStore.regenerateKnowledgeGraph(currentChapter.value.chapter_id)
    const data = await noteStore.fetchKnowledgeGraph(currentChapter.value.chapter_id)
    if (data) {
      knowledgeGraph.value = data
      ElMessage.closeAll()
      ElMessage.success('知识图谱已更新')
      nextTick(() => {
        renderKnowledgeGraph()
      })
    }
  } catch (error) {
    if (error.response?.status === 403) {
      console.error('Token余额不足，请充值后继续使用', error)
      kgError.value = 'Token余额不足，请充值后继续使用'
      ElMessage.closeAll()
      ElMessage.error('Token余额不足，请充值后继续使用')
    } else{
      console.error('重新生成知识图谱失败:', error)
      kgError.value = '重新生成知识图谱失败，请稍后重试'
      ElMessage.closeAll()
      ElMessage.error('重新生成知识图谱失败，请稍后重试')
    }
  } finally {
    kgLoading.value = false
  }
}

// 添加新的响应式变量
const summaryContent = ref('')
const isLoadingSummary = ref(false)
const summaryError = ref('')

// 修改生成笔记总结的方法
const generateSummary = async () => {
  if (!currentChapter.value) {
    ElMessage.warning('请先选择章节')
    return
  }

  isLoadingSummary.value = true
  summaryError.value = ''
  summaryContent.value = ''

  try {
    const response = await fetch(`http://localhost:5000/notes_summary_service/notes/summary/generate/${currentChapter.value.chapter_id}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${useUserStore().accessToken}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') break

          summaryContent.value += data
        }
      }
    }
  } catch (error) {
    summaryError.value = '生成笔记总结失败，请稍后重试'
    console.error('生成笔记总结失败:', error)
  } finally {
    isLoadingSummary.value = false
  }
}

// 修改生成知识图谱的方法
const generateKnowledgeGraph = async () => {
  if (!currentChapter.value) {
    ElMessage.warning('请先选择章节')
    return
  }

  kgDrawerVisible.value = true
  kgLoading.value = true
  kgError.value = ''

  try {
    const response = await fetch(`http://localhost:5000/notes_summary_service/knowledge_graph/generate/${currentChapter.value.chapter_id}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${useUserStore().accessToken}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error(`请求失败: ${response.status}`)
    }

    // 知识图谱生成完成后，立即获取并渲染
    const data = await noteStore.fetchKnowledgeGraph(currentChapter.value.chapter_id)
    if (data) {
      knowledgeGraph.value = data
      nextTick(() => {
        renderKnowledgeGraph()
      })
    }
  } catch (error) {
    kgError.value = '生成知识图谱失败，请稍后重试'
    console.error('生成知识图谱失败:', error)
  } finally {
    kgLoading.value = false
  }
}

// 修改重新生成图谱的方法
const regenerateKnowledgeGraph = async () => {
  try {
    isRegenerating.value = true;
    const response = await noteStore.regenerateKnowledgeGraph(currentChapter.value.chapter_id);
    if (response) {
      // 更新图谱数据
      graphData.value = {
        nodes: response.items.map(item => ({
          id: item.id,
          label: item.name,
          title: item.description
        })),
        edges: response.relations.map(relation => ({
          id: relation.id,
          from: relation.source,
          to: relation.target,
          label: relation.relation_type
        }))
      };
      ElMessage.success('知识图谱已重新生成');
    }
  } catch (error) {
    console.error('重新生成知识图谱失败:', error);
    ElMessage.error('重新生成知识图谱失败，请稍后重试');
  } finally {
    isRegenerating.value = false;
  }
};




// 修改resize监听部分
const handleResize = () => {
  if (kgContainer.value && knowledgeGraph.value) {
    requestAnimationFrame(renderKnowledgeGraph)
  }
};

onMounted(() => {
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});

// 配置marked以支持数学公式
marked.setOptions({
  renderer: new marked.Renderer(),
  highlight: function(code, lang) {
    return code;
  },
  pedantic: false,
  gfm: true,
  breaks: true,
  sanitize: false,
  smartypants: false,
  xhtml: false
})

// 修改数学公式渲染函数
const renderMath = (text, displayMode = false) => {
  try {
    return katex.renderToString(text, {
      displayMode: displayMode,
      throwOnError: false,
      strict: false,
      trust: true,
      macros: {
        "\\RR": "\\mathbb{R}",
        "\\NN": "\\mathbb{N}",
        "\\ZZ": "\\mathbb{Z}",
        "\\CC": "\\mathbb{C}"
      },
      fleqn: false,
      leqno: false,
      output: "html"
    })
  } catch (e) {
    console.error('Math rendering error:', e)
    return text
  }
}

// 修改Markdown渲染函数
const renderMarkdown = (text) => {
  if (!text) return ''

  // 先提取所有数学公式并保存
  const mathExpressions = []
  let mathId = 0

  // 用占位符替换所有数学公式
  text = text.replace(/\\\[([\s\S]*?)\\\]|\\\(([\s\S]*?)\\\)/g, (match, display, inline) => {
    const formula = display || inline
    const isDisplay = !!display
    const placeholder = `MATH_PLACEHOLDER_${mathId}`
    mathExpressions.push({
      placeholder,
      formula,
      isDisplay
    })
    mathId++
    return placeholder
  })

  // 渲染Markdown
  let html = marked(text)

  // 还原数学公式
  mathExpressions.forEach(({ placeholder, formula, isDisplay }) => {
    const renderedMath = renderMath(formula, isDisplay)
    html = html.replace(placeholder, renderedMath)
  })

  return html
}

// 修改渲染内容函数
const renderContent = (text) => {
  return renderMarkdown(text)
}
</script>
<style scoped>
/* 优化数学公式相关样式 */
:deep(.katex-display) {
  overflow-x: auto;
  overflow-y: hidden;
  padding: 1em 0;
  margin: 0.5em 0;
  text-align: center;
}

:deep(.katex) {
  font-size: 1.1em;
  line-height: 1.2;
  white-space: normal;
  text-indent: 0;
}

:deep(.katex-html) {
  white-space: normal;
  text-align: left;
}

/* 添加浮动元素清除样式 */
:deep(.katex-display::after) {
  content: "";
  display: table;
  clear: both;
}

/* 确保数学公式容器有足够的空间 */
:deep(.katex-display > .katex) {
  display: inline-block;
  white-space: nowrap;
  max-width: 100%;
  text-align: initial;
}

/* 解决长公式溢出问题 */
:deep(.katex-display > .katex > .katex-html) {
  display: block;
  position: relative;
  overflow-x: auto;
  overflow-y: hidden;
  text-align: center;
  width: 100%;
}

/* 针对笔记内容中数学公式的特殊处理 */
.note-text :deep(.katex-display) {
  margin: 1em 0;
}

.note-text :deep(.katex) {
  font-size: 1.05em;
}

/* 修复表格内数学公式显示 */
:deep(table .katex) {
  font-size: 1em;
}

/* 基础布局 */
.dashboard-container {
  display: flex;
  gap: 24px;
  padding: 24px;
  height: calc(100vh - 64px);
  background: #f5f7fa;
}

/* 左侧边栏 */
.side-widgets {
  width: 360px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 900px;
  margin-left: 30px;
}

/* 卡片基础样式 */
.widget-card {
  background: white;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  flex-shrink: 0;
  min-height: 140px;
}

/* 修改统计卡片样式 */
.stats-card {
  .stats-header {
    margin-bottom: 12px;
    padding: 0 8px;

    h3 {
      font-size: 15px;
      color: #303133;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 8px;

      &::before {
        content: '';
        display: block;
        width: 3px;
        height: 15px;
        background: #6c5dd3;
        border-radius: 2px;
      }
    }
  }

  .statistics-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    padding: 8px;

    .stat-item {
      padding: 12px 10px;
      border-radius: 12px;
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      transition: all 0.3s ease;
      background: #f5f7fa;

      &:hover {
        transform: translateY(-2px);
      }

      &.total {
        background: #f5f7fa;
        color: #409EFF;
      }

      &.clear {
        background: #f5f7fa;
        color: #67C23A;
      }

      &.vague {
        background: #f5f7fa;
        color: #E6A23C;
      }

      &.unclear {
        background: #f5f7fa;
        color: #F56C6C;
      }

      .stat-value {
        font-size: 22px;
        font-weight: 600;
        line-height: 1;
      }

      .stat-label {
        font-size: 13px;
        opacity: 0.9;
        font-weight: 500;
        color: #606266;
      }
    }
  }
}

/* 章节列表卡片样式优化 */
.chapters-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 300px);
  overflow: hidden;

  .widget-header {
    padding: 16px 24px;
    border-bottom: 1px solid #ebeef5;
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      font-size: 16px;
      font-weight: 600;
      color: #303133;
      margin: 0;
    }

    /* 新建章节按钮样式 */
    .create-chapter-btn {
      padding: 6px 12px;
      font-size: 13px;
      border-radius: 8px;
      background: linear-gradient(135deg, #6c5dd3, #8674ff);
      border: none;
      color: white;
      display: flex;
      align-items: center;
      gap: 4px;
      transition: all 0.3s ease;

      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(108, 93, 211, 0.2);
      }

      .el-icon {
        font-size: 14px;
      }
    }
  }

  .chapters-list {
    flex: 1;
    overflow: hidden;
    padding: 16px 20px;
  }

  :deep(.el-collapse-item__header) {
    padding: 14px 20px;
    min-height: 50px;
  }

  :deep(.el-collapse-item__content) {
    padding: 16px 20px;
  }
}

/* 其他样式保持不变 */
.notes-content {
  flex: 1;
  padding: 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  min-width: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 20px;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.summary-button {
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.custom-add-button {
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.notes-list {
  padding: 0 20px;
  padding-bottom: 24px;
}

.category-tabs {
  position: sticky;
  top: 0;
  background: white;
  z-index: 1;
  padding-top: 20px;
}

.notes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  padding: 16px 0;
  margin-bottom: 20px;
}

.note-card {
  height: fit-content;
  margin-bottom: 0;
  border-radius: 10px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.note-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.1);
}

.note-card.理解 {
  border-top: 3px solid #6c5dd3;
}

.note-card.模糊 {
  border-top: 3px solid #e6a23c;
}

.note-card.不理解 {
  border-top: 3px solid #f56c6c;
}

.note-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  min-height: 32px; /* 添加最小高度 */
}

.note-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap; /* 允许换行 */
}

.note-date {
  color: #909399;
  font-size: 13px;
  white-space: nowrap;
}

.note-level {
  margin: 0;
  white-space: nowrap;
}

.note-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
  white-space: nowrap;
  flex-shrink: 0; /* 防止按钮被压缩 */
}

/* 优化按钮组样式 */
:deep(.el-button-group) {
  display: flex;
  gap: 4px;
  flex-shrink: 0; /* 防止按钮组被压缩 */
}

:deep(.el-button-group .el-button) {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px; /* 减小内边距 */
  margin: 0;
  font-size: 12px;
  min-width: auto; /* 移除最小宽度限制 */
}

:deep(.el-button-group .el-button:hover) {
  background-color: var(--el-button-hover-bg-color);
  opacity: 0.8;
}

/* 确保按钮图标和文字不会换行 */
:deep(.el-button-group .el-button .el-icon) {
  margin-right: 2px; /* 减小图标右边距 */
}

:deep(.el-button-group .el-button span) {
  white-space: nowrap;
}

.note-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.note-image {
  max-height: 180px;
  object-fit: contain;
  border-radius: 4px;
}

.note-audio {
  width: 100%;
}

.image-description,
.audio-description {
  color: #606266;
  font-style: italic;
  font-size: 13px;
}

.note-text {
  white-space: pre-wrap;
  line-height: 1.5;
  font-size: 14px;
}

/* 对话框样式 */
:deep(.custom-dialog) {
  border-radius: 16px;
  overflow: hidden;
}

:deep(.custom-dialog .el-dialog__header) {
  margin: 0;
  padding: 20px 24px;
  border-bottom: 1px solid #ebeef5;
}

:deep(.custom-dialog .el-dialog__title) {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

:deep(.custom-dialog .el-dialog__body) {
  padding: 24px;
}

:deep(.custom-dialog .el-dialog__footer) {
  padding: 16px 24px;
  border-top: 1px solid #ebeef5;
}

/* 表单样式 */
:deep(.el-form-item__label) {
  padding-bottom: 8px;
  font-weight: 500;
  color: #303133;
}

:deep(.el-input__wrapper),
:deep(.el-select),
:deep(.el-cascader) {
  --el-input-hover-border-color: #6c5dd3;
  --el-input-focus-border-color: #6c5dd3;
}

:deep(.el-input__wrapper.is-focus),
:deep(.el-cascader.is-focus) {
  box-shadow: 0 0 0 1px #6c5dd3;
}

/* 确认按钮样式 */
.custom-confirm-btn {
  background: linear-gradient(135deg, #6c5dd3, #8674ff);
  border: none;
  color: white;
  padding: 8px 20px;
  border-radius: 8px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(108, 93, 211, 0.2);
  }
}

/* 上传区域样式 */
:deep(.el-upload-dragger) {
  width: 100%;
  height: 120px;
  border: 2px dashed #6c5dd3;
  border-radius: 8px;

  &:hover {
    border-color: #8674ff;
  }
}

/* 选择器选项样式 */
:deep(.el-select-dropdown__item.selected) {
  color: #6c5dd3;
  font-weight: bold;
}

:deep(.el-cascader-node.in-active-path),
:deep(.el-cascader-node.is-active) {
  color: #6c5dd3;
}

/* 标签样式 */
:deep(.el-tag) {
  border-radius: 4px;
  padding: 0 8px;
  &.el-tag--success {
    --el-tag-bg-color: rgba(108, 93, 211, 0.1);
    --el-tag-border-color: rgba(108, 93, 211, 0.2);
    --el-tag-text-color: #6c5dd3;
  }
}

.subject-filter {
  margin: 16px 0;
  padding: 0 16px;
  display: flex;
  justify-content: center;
}

:deep(.el-radio-group) {
  background: #f5f7fa;
  padding: 4px;
  border-radius: 8px;
  display: flex;
  gap: 4px;
}

:deep(.el-radio-button__inner) {
  border: none !important;
  background: transparent;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s ease;
}

:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: white !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
  color: #6c5dd3 !important;
}

/* 滚动区域样式 */
.notes-scrollbar {
  flex: 1;
  height: 0;
  overflow: hidden;
  margin: 0 -24px;
  padding: 0 24px;
}

/* 确保标签页不会遮挡圆角 */
:deep(.el-tabs__content) {
  overflow: visible;
}

/* 优化滚动条样式 */
:deep(.el-scrollbar__bar) {
  opacity: 0.3;
  transition: opacity 0.2s;
}

:deep(.el-scrollbar__bar:hover) {
  opacity: 0.8;
}

/* 确保滚动条不会影响圆角显示 */
:deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
  margin-bottom: 0 !important;
}

/* 优化布局容器 */
.dashboard-container {
  height: 100vh;
  display: flex;
  gap: 24px;
  padding: 24px;
  background: #f5f7fa;
  overflow: hidden;
}

/* 调整标签大小 */
:deep(.el-tag) {
  font-size: 12px;
  height: 22px;
  line-height: 22px;
}

/* 优化章节项样式 */
.chapter-item {
  margin-bottom: 16px;

  &:last-child {
    margin-bottom: 0;
  }
}

/* 修改章节标题样式 */
.chapter-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 8px 0;
}

.chapter-title-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.subject-tag {
  flex-shrink: 0;
  font-size: 12px;
  padding: 0 8px;
  height: 24px;
  line-height: 24px;
  border-radius: 4px;
}

.chapter-name {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 修改章节内容样式 */
.chapter-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  margin: 8px 0;
}

.chapter-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.note-count {
  font-size: 12px;
  color: #909399;
  background: #f4f4f5;
  border: none;
}

.chapter-actions {
  display: flex;
  gap: 16px;
  padding-top: 8px;
  border-top: 1px solid #ebeef5;
}

.action-button {
  font-size: 13px;
  height: 28px;
  padding: 0 12px;
  border-radius: 4px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-button:hover {
  transform: translateY(-1px);
}

.action-button .el-icon {
  margin-right: 4px;
}

/* 修改折叠面板样式 */
:deep(.el-collapse-item__header) {
  font-size: 14px;
  padding: 12px 16px;
  background: #ffffff;
  border-radius: 8px;
  margin-bottom: 4px;
}

:deep(.el-collapse-item__content) {
  padding: 0 16px;
}

:deep(.el-collapse-item__wrap) {
  background: transparent;
}

.summary-container {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.summary-content {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
}

.markdown-content {
  line-height: 1.6;
  min-height: 200px;
  max-height: calc(100vh - 200px);
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
  border-bottom: 1px solid #eaecef;
  padding-bottom: 0.3em;
}

.markdown-content :deep(h1) {
  font-size: 1.5em;
}

.markdown-content :deep(h2) {
  font-size: 1.3em;
}

.markdown-content :deep(h3) {
  font-size: 1.1em;
}

.markdown-content :deep(p) {
  margin-bottom: 16px;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 24px;
  margin-bottom: 16px;
}

.markdown-content :deep(li) {
  margin-bottom: 8px;
}

.markdown-content :deep(blockquote) {
  padding: 0 1em;
  color: #6a737d;
  border-left: 0.25em solid #dfe2e5;
  margin: 0 0 16px 0;
}

.markdown-content :deep(code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27,31,35,0.05);
  border-radius: 3px;
}

.markdown-content :deep(pre) {
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background-color: #f6f8fa;
  border-radius: 3px;
  margin-bottom: 16px;
}

.markdown-content :deep(pre code) {
  padding: 0;
  background-color: transparent;
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  gap: 16px;
}

.loading-icon {
  animation: rotating 2s linear infinite;
  font-size: 24px;
  color: #6c5dd3;
}

.loading-text {
  color: #606266;
  font-size: 14px;
}

.empty-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: #909399;
  font-size: 14px;
}

.regenerate-button {
  margin-top: auto;
  width: 100%;
  background: linear-gradient(to right, #6c5dd3, #8e6cff);
  border: none;
  color: white;
  height: 40px;
  border-radius: 8px;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 在样式部分添加 */
.kg-container {
  position: relative;
  height: calc(100vh - 60px);
  padding: 0;
  background: #f8f9fa;
  border-radius: 12px;
  overflow: hidden;
}

.kg-content {
  height: 100%;
  min-height: 400px;
  border: none;
  overflow: auto;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
}

.kg-graph {
  width: 100%;
  height: 100%;
  min-height: 400px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

:deep(.el-drawer__body) {
  height: calc(100% - 55px) !important;
  padding: 0 !important;
  background: #f8f9fa;
}

.loading-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 9;
  background: rgba(255, 255, 255, 0.9);
  padding: 30px 40px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.error-message {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(255, 255, 255, 0.9);
  padding: 30px 40px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  text-align: center;
  max-width: 80%;
}

.error-message {
  color: #f56c6c;
  font-size: 14px;
  line-height: 1.6;
}

.kg-button {
  background: linear-gradient(135deg, #6c5dd3 0%, #8674ff 100%);
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  color: white;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(108, 93, 211, 0.2);
}

.kg-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.3);
}

.kg-actions {
  padding: 16px 20px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: flex-end;
  background: white;
  border-radius: 12px 12px 0 0;
}

.regenerate-button {
  background: linear-gradient(135deg, #6c5dd3 0%, #8674ff 100%);
  border: none;
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s ease;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(108, 93, 211, 0.2);
}

.regenerate-button:hover:not(.is-disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(108, 93, 211, 0.3);
}

/* 知识图谱节点样式 */
:deep(.node circle) {
  fill: #6c5dd3;
  stroke: #8674ff;
  stroke-width: 2px;
  transition: all 0.3s ease;
}

:deep(.node circle:hover) {
  fill: #8674ff;
  stroke: #6c5dd3;
  stroke-width: 3px;
  r: 15;
}

:deep(.node text) {
  font-size: 12px;
  font-weight: 500;
  fill: #303133;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

:deep(.link) {
  stroke: #dcdfe6;
  stroke-width: 1.5px;
  stroke-opacity: 0.6;
  transition: all 0.3s ease;
}

:deep(.link:hover) {
  stroke: #6c5dd3;
  stroke-width: 2px;
  stroke-opacity: 0.8;
}

:deep(.link-label) {
  font-size: 10px;
  fill: #606266;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

/* 知识图谱缩放控制 */
:deep(.zoom-controls) {
  position: absolute;
  bottom: 20px;
  right: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 10;
}

:deep(.zoom-button) {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: white;
  border: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.zoom-button:hover) {
  background: #f5f7fa;
  border-color: #6c5dd3;
  color: #6c5dd3;
}

/* 知识图谱搜索框 */
:deep(.kg-search) {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 10;
  background: white;
  padding: 8px 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.kg-search input) {
  border: none;
  outline: none;
  font-size: 14px;
  color: #303133;
  background: transparent;
  width: 200px;
}

:deep(.kg-search input::placeholder) {
  color: #909399;
}

/* 知识图谱图例 */
:deep(.kg-legend) {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.kg-legend-item) {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

:deep(.kg-legend-item:last-child) {
  margin-bottom: 0;
}

:deep(.kg-legend-color) {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

:deep(.kg-legend-label) {
  font-size: 12px;
  color: #606266;
}
</style>
