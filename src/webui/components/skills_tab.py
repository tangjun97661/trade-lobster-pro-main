import gradio as gr

from src.webui.webui_manager import WebuiManager


def create_skills_tab(webui_manager: WebuiManager):
    gr.HTML(
        value="""
        <div class="skills-page" id="lobster-skills-page">
          <div class="skills-toolbar">
            <div class="skills-title">
              <h2>业务指令集（Skills）</h2>
              <div class="skills-subtitle">在本地浏览器保存与管理业务场景指令，支持新增/修改/删除/执行</div>
            </div>
            <button class="skills-btn skills-btn-primary" type="button" id="lobster-skill-create-btn">+ 新增业务指令</button>
          </div>

          <div class="skills-grid" id="lobster-skills-grid"></div>

          <div class="skills-modal-backdrop" id="lobster-skills-modal" aria-hidden="true">
            <div class="skills-modal">
              <div class="skills-modal-header">
                <div class="skills-modal-title" id="lobster-skills-modal-title">新增业务指令</div>
                <button class="skills-btn skills-btn-ghost" type="button" id="lobster-skills-modal-close">关闭</button>
              </div>
              <div class="skills-modal-body">
                <div class="skills-form-row">
                  <div class="skills-form-field">
                    <label class="skills-label" for="lobster-skill-id">ID</label>
                    <input class="skills-input" id="lobster-skill-id" placeholder="skills-xxx" />
                  </div>
                  <div class="skills-form-field">
                    <label class="skills-label" for="lobster-skill-name">名称</label>
                    <input class="skills-input" id="lobster-skill-name" placeholder="业务指令名称" />
                  </div>
                </div>
                <div class="skills-form-field">
                  <label class="skills-label" for="lobster-skill-desc">简述</label>
                  <input class="skills-input" id="lobster-skill-desc" placeholder="一句话描述该技能" />
                </div>
                <div class="skills-form-field">
                  <label class="skills-label" for="lobster-skill-prompt">Prompt</label>
                  <textarea class="skills-textarea" id="lobster-skill-prompt" rows="10" placeholder="在此填写完整的业务指令 Prompt"></textarea>
                </div>
                <div class="skills-form-field">
                  <div class="skills-fields-header">
                    <label class="skills-label">扩展字段（required_fields）</label>
                    <button class="skills-btn skills-btn-secondary" type="button" id="lobster-skill-field-add">+ 扩展字段</button>
                  </div>
                  <div class="skills-fields-list" id="lobster-skill-fields"></div>
                </div>
              </div>
              <div class="skills-modal-footer">
                <button class="skills-btn skills-btn-secondary" type="button" id="lobster-skills-modal-cancel">取消</button>
                <button class="skills-btn skills-btn-primary" type="button" id="lobster-skills-modal-save">保存</button>
              </div>
            </div>
          </div>

          <div class="skills-modal-backdrop" id="lobster-skills-confirm" aria-hidden="true">
            <div class="skills-modal skills-modal-sm">
              <div class="skills-modal-header">
                <div class="skills-modal-title">确认删除</div>
                <button class="skills-btn skills-btn-ghost" type="button" id="lobster-skills-confirm-close">关闭</button>
              </div>
              <div class="skills-modal-body">
                <div class="skills-confirm-text" id="lobster-skills-confirm-text">确认删除该业务指令？</div>
              </div>
              <div class="skills-modal-footer">
                <button class="skills-btn skills-btn-secondary" type="button" id="lobster-skills-confirm-cancel">取消</button>
                <button class="skills-btn skills-btn-danger" type="button" id="lobster-skills-confirm-ok">删除</button>
              </div>
            </div>
          </div>

          <div class="skills-toast" id="lobster-skills-toast" aria-hidden="true"></div>
        </div>
        """,
        elem_id="lobster_skills_root",
    )
