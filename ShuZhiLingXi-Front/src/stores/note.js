import { defineStore } from 'pinia'
import axios from '../utils/axios'
import { ElMessage } from 'element-plus'
import { nextTick } from 'vue'
import http from 'http'
import https from 'https'

export const useNoteStore = defineStore('note', {
  state: () => ({
    chapters: [],
    currentChapter: null,
    notes: [],
    categories: [],
    subjectCategories: [],
    lastFetchTime: null,
    statistics: {
      notes_count: 0,
      clear_notes_count: 0,
      vague_notes_count: 0,
      unclear_notes_count: 0
    },
    noteSummary: '',
    isLoadingSummary: false,
    hasExistingSummary: false,
    summaries: {}  // 存储章节ID到总结内容的映射
  }),

  getters: {
    // 添加一个 getter 来获取分类名称
    getCategoryName: (state) => (categoryId) => {
      const category = state.categories.find(c => c.category_id === Number(categoryId));
      return category ? category.name : '未分类';
    }
  },

  actions: {
    // 获取所有笔记章节
    async fetchChapters() {
      try {
        // 先确保有分类数据
        if (this.categories.length === 0) {
          await this.getCategories();
        }

        const response = await axios.get('/notes_service/chapter/list')
        if (response.status === 200) {
          // 处理章节数据，添加分类名称
          this.chapters = (response.data.data || []).map(chapter => ({
            ...chapter,
            categoryName: this.getCategoryName(chapter.category)
          }));
          this.lastFetchTime = new Date()
        }
      } catch (error) {
        console.error('获取章节失败:', error)
        throw error
      }
    },

    // 如果数据太旧才重新获取
    async getChapters() {
      // 直接获取最新数据，不使用缓存
      await this.fetchChapters()
      return this.chapters
    },

    // 创建笔记章节
    async createChapter(chapterData) {
      try {
        const response = await axios.post('/notes_service/chapter/create', chapterData)
        if (response.status === 200) {
          // 强制刷新章节列表
          await this.fetchChapters()
          // 确保新章节显示在列表中并带有正确的分类名称
          const newChapter = this.chapters.find(c =>
              c.name === chapterData.name &&
              c.category === chapterData.category
          );
          if (newChapter) {
            this.setCurrentChapter(newChapter)
          }
          ElMessage.success('创建章节成功')
          return response.data
        }
      } catch (error) {
        console.error('创建章节失败:', error)
        ElMessage.error(error.response?.data?.msg || '创建章节失败')
        throw error
      }
    },

    // 更新章节
    async updateChapter(chapterId, chapterData) {
      try {
        const response = await axios.put(`/notes_service/chapter/edit/${chapterId}`, chapterData)
        if (response.status === 200) {
          await this.fetchChapters()
          ElMessage.success('更新章节成功')
          return response.data
        }
      } catch (error) {
        console.error('更新章节失败:', error)
        ElMessage.error(error.response?.data?.msg || '更新章节失败')
        throw error
      }
    },

    // 删除章节
    async deleteChapter(chapterId) {
      try {
        // 1. 先保存要删除的章节信息，用于可能的回滚
        const chapterToDelete = this.chapters.find(c => c.chapter_id === chapterId);
        const chapterNotes = this.notes.filter(note => note.chapter_id === chapterId);
        const originalChapters = [...this.chapters];
        const originalNotes = [...this.notes];
        const originalStatistics = { ...this.statistics };
        const originalCurrentChapter = this.currentChapter;

        // 2. 立即更新前端状态
        this.chapters = this.chapters.filter(chapter => chapter.chapter_id !== chapterId);

        if (this.currentChapter?.chapter_id === chapterId) {
          this.currentChapter = null;
          this.notes = [];
        }

        // 3. 更新统计信息
        if (chapterToDelete) {
          this.statistics.notes_count = Math.max(0,
              this.statistics.notes_count - (chapterToDelete.note_count || 0)
          );

          chapterNotes.forEach(note => {
            switch (note.comprehension_level) {
              case '理解':
                this.statistics.clear_notes_count = Math.max(0,
                    this.statistics.clear_notes_count - 1
                );
                break;
              case '模糊':
                this.statistics.vague_notes_count = Math.max(0,
                    this.statistics.vague_notes_count - 1
                );
                break;
              case '不理解':
                this.statistics.unclear_notes_count = Math.max(0,
                    this.statistics.unclear_notes_count - 1
                );
                break;
            }
          });
        }

        // 4. 尝试发送后端请求
        try {
          await axios.put(`/notes_service/chapter/delete/${chapterId}`);
          ElMessage.success('章节删除成功');
        } catch (error) {
          console.error('删除章节请求失败:', error);

          // 5. 如果是服务器错误（500），继续保持前端的删除状态
          if (error.response?.status === 500) {
            ElMessage({
              message: '章节已在前端删除，但服务器同步失败。下次刷新时可能会重新出现。',
              type: 'warning',
              duration: 5000
            });
            return { success: true };
          }

          // 6. 如果是其他错误，回滚前端状态
          this.chapters = originalChapters;
          this.notes = originalNotes;
          this.statistics = originalStatistics;
          this.currentChapter = originalCurrentChapter;

          ElMessage.error('删除章节失败，已恢复原状态');
          return { success: false };
        }

        return { success: true };
      } catch (error) {
        console.error('删除章节操作失败:', error);
        ElMessage.error('删除章节操作失败');
        return { success: false };
      }
    },

    // 获取章节的笔记
    async fetchNotes(chapterId) {
      try {
        const response = await axios.get(`/notes_service/note/list/${chapterId}`)
        if (response.status === 200) {
          // 确保笔记数据包含理解程度
          this.notes = (response.data.data || []).map(note => ({
            ...note,
            comprehension_level: note.comprehension_level || '理解' // 设置默认值
          }))

          // 更新统计信息
          this.updateStatistics()
        }
      } catch (error) {
        console.error('获取笔记失败:', error)
        throw error
      }
    },

    // 创建笔记
    async createNote(noteData) {
      try {
        // 确保 comprehension_level 字段存在
        const submitData = {
          ...noteData,
          comprehension_level: noteData.comprehension_level || '理解'
        };

        const response = await axios.post('/notes_service/note/create', submitData)
        if (response.status === 200) {
          await this.fetchNotes(noteData.chapter_id)
          this.updateStatistics()

          const chapter = this.chapters.find(c => c.chapter_id === noteData.chapter_id)
          if (chapter) {
            chapter.note_count = (chapter.note_count || 0) + 1
          }

          ElMessage.success('创建笔记成功')
          return response.data
        }
      } catch (error) {
        console.error('创建笔记失败:', error)
        ElMessage.error(error.response?.data?.msg || '创建笔记失败')
        throw error
      }
    },

    // 更新笔记
    async updateNote(noteId, noteData) {
      try {
        // 确保 comprehension_level 字段存在
        const submitData = {
          ...noteData,
          comprehension_level: noteData.comprehension_level || '理解'
        };

        const response = await axios.put(`/notes_service/note/edit/${noteId}`, submitData)
        if (response.status === 200) {
          if (this.currentChapter) {
            await this.fetchNotes(this.currentChapter.chapter_id)
          }
          ElMessage.success('更新笔记成功')
          return response.data
        }
      } catch (error) {
        console.error('更新笔记失败:', error)
        ElMessage.error(error.response?.data?.msg || '更新笔记失败')
        throw error
      }
    },

    // 删除笔记
    async deleteNote(noteId) {
      try {
        const response = await axios.put(`/notes_service/note/delete/${noteId}`)
        if (response.status === 200) {
          // 更新本地数据
          this.notes = this.notes.filter(note => note.note_id !== noteId)
          this.updateStatistics()

          // 更新章节的笔记计数
          if (this.currentChapter) {
            const chapter = this.chapters.find(c => c.chapter_id === this.currentChapter.chapter_id)
            if (chapter && chapter.note_count > 0) {
              chapter.note_count--
            }
          }
          ElMessage.success('删除笔记成功')
          return response.data
        }
      } catch (error) {
        // 即使后端返回错误，也尝试更新前端状态
        this.notes = this.notes.filter(note => note.note_id !== noteId)
        this.updateStatistics()
        console.error('删除笔记失败:', error)
        return { success: true }
      }
    },

    // 获取分类并处理科目分类
    async getCategories() {
      try {
        const response = await axios.get('/notes_service/categories');
        if (response.status === 200) {
          this.categories = response.data.data || [];
          // 处理科目分类
          this.subjectCategories = this.categories
              .filter(cat => !cat.is_deleted)
              .map(cat => ({
                value: cat.category_id,
                label: cat.name,
                type: this.getSubjectType(cat.name)
              }));
        }
      } catch (error) {
        console.error('获取分类失败:', error);
        ElMessage.error(error.response?.data?.msg || '获取分类失败');
        throw error;
      }
    },

    // 获取科目类型
    getSubjectType(name) {
      const lowerName = name.toLowerCase();
      if (lowerName.includes('语文')) return 'chinese';
      if (lowerName.includes('数学')) return 'math';
      if (lowerName.includes('英语')) return 'english';
      return 'other';
    },

    // 设置当前章节
    setCurrentChapter(chapter) {
      this.currentChapter = chapter
    },

    // 更新统计信息
    updateStatistics() {
      // 只统计未删除的笔记
      const activeNotes = this.notes.filter(note => !note.is_deleted)

      // 重置统计数据
      this.statistics = {
        notes_count: activeNotes.length,
        clear_notes_count: 0,
        vague_notes_count: 0,
        unclear_notes_count: 0
      }

      // 统计各类型笔记数量
      activeNotes.forEach(note => {
        switch (note.comprehension_level) {
          case '理解':
            this.statistics.clear_notes_count++
            break
          case '模糊':
            this.statistics.vague_notes_count++
            break
          case '不理解':
            this.statistics.unclear_notes_count++
            break
        }
      })

      // 打印日志以便调试
      console.log('Updated statistics:', this.statistics)
    },

    // 添加新的 action 来处理分类树结构
    async getFormattedCategories() {
      try {
        await this.getCategories();
        return this.formatCategoryTree(this.categories);
      } catch (error) {
        console.error('获取格式化分类失败:', error);
        throw error;
      }
    },

    // 将分类数据格式化为树形结构
    formatCategoryTree(categories) {
      if (!Array.isArray(categories)) return [];
      return categories
          .filter(cat => !cat.is_deleted)
          .map(cat => ({
            value: cat.category_id,
            label: cat.name,
            type: this.getSubjectType(cat.name)
          }));
    },

    // 获取已存在的笔记总结
    async getExistingSummary(chapterId) {
      try {
        const response = await axios.get(`/notes_summary_service/notes/summary/get/${chapterId}`)
        return response.data
      } catch (error) {
        if (error.response?.status === 404) {
          return null
        }
        throw error
      }
    },

    // 更新总结内容
    updateSummary(chapterId, summary) {
      this.summaries[chapterId] = summary
    },

    async generateStreamingSummary(chapterId) {
      try {
        this.isLoadingSummary = true;
        this.summary = '';
        let buffer = '';

        const response = await axios.post(
          `/notes_summary_service/notes/summary/generate/${chapterId}`,
          {},
          {
            responseType: 'text',
            headers: {
              'Accept': 'text/event-stream',
            },
            timeout: 60000,
            onDownloadProgress: (progressEvent) => {
              const rawText = progressEvent.event.target.responseText;
              if (!rawText || rawText === buffer) return; // 如果没有新数据，直接返回

              // 只处理新增的部分
              const newContent = rawText.slice(buffer.length);
              buffer = rawText; // 更新buffer为当前完整内容

              // 处理新增内容
              const lines = newContent.split('\n');
              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  const data = line.slice(6);
                  if (data === '[DONE]') {
                    this.isLoadingSummary = false;
                    break;
                  }
                  // 直接设置summary而不是追加
                  this.summary = buffer.split('\n')
                    .filter(l => l.startsWith('data: ') && l.slice(6) !== '[DONE]')
                    .map(l => l.slice(6))
                    .join('');
                }
              }
            }
          }
        );
        return this.summary;
      } catch (error) {
        console.error('生成总结失败:', error);
        this.isLoadingSummary = false;
        if (error.response?.status === 403) {
          ElMessage.error('Token余额不足，请充值后继续使用');
        } else if (error.response?.status === 429) {
          ElMessage.error('请求过于频繁，请稍后再试');
        } else {
          ElMessage.error('生成总结失败，请稍后重试');
        }
        throw error;
      }
    },

    async fetchKnowledgeGraph(chapterId) {
      try {
        const response = await axios.get(`/notes_summary_service/knowledge_graph/get/${chapterId}`)
        if (response.status === 200) {
          return response.data.data
        }
      } catch (error) {
        console.error('获取知识图谱失败:', error)
        ElMessage.error('获取知识图谱失败')
        throw error
      }
    },

    async regenerateKnowledgeGraph(chapterId) {
      try {
        const response = await axios.post(
          `/notes_summary_service/knowledge_graph/generate/${chapterId}`,
          {},
          {
            timeout: 60000
          }
        )

        if (response.status === 200 && response.data.data) {
          return response.data.data
        } else {
          throw new Error(response.data.msg || '生成知识图谱失败')
        }
      } catch (error) {
        console.error('重新生成知识图谱失败:', error)
        if (error.response?.status === 403) {
          ElMessage.error('Token余额不足，请充值后继续使用');
        }
        throw error
      }
    }
  }
})
