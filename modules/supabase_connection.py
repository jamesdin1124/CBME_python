import os
import hashlib
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st

class SupabaseConnection:
    """
    Supabase 資料庫連接類別
    用於處理與 Supabase 資料庫的連接和操作
    """

    def __init__(self):
        """
        初始化 Supabase 連接
        從環境變數中讀取 Supabase URL 和 API Key
        """
        load_dotenv()
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError("請在 .env 檔案中設置 SUPABASE_URL 和 SUPABASE_KEY")

        self.client: Client = create_client(self.url, self.key)

    def get_client(self) -> Client:
        """
        獲取 Supabase 客戶端實例

        Returns:
            Client: Supabase 客戶端實例
        """
        return self.client

    def test_connection(self) -> bool:
        """
        測試與 Supabase 的連接是否正常

        Returns:
            bool: 連接是否成功
        """
        try:
            # 嘗試執行一個簡單的查詢來測試連接
            self.client.table('users').select('count').execute()
            return True
        except Exception as e:
            print(f"Supabase 連接測試失敗: {str(e)}")
            return False

    # =============================================
    # 兒科 CCC 評估系統方法
    # =============================================

    def fetch_pediatric_evaluations(self, filters=None):
        """
        查詢兒科評核記錄

        Args:
            filters (dict, optional): 過濾條件，支援的 key：
                - evaluation_type: 'technical_skill' | 'meeting_report' | 'epa'
                - evaluated_resident: 住院醫師姓名
                - evaluator_teacher: 評核教師姓名
                - date_from: 起始日期 (str 'YYYY-MM-DD')
                - date_to: 結束日期 (str 'YYYY-MM-DD')
                - department: 科別名稱（用於科別隔離）

        Returns:
            list[dict]: 評核記錄列表，空列表表示無資料
        """
        try:
            query = self.client.table('pediatric_evaluations') \
                .select('*') \
                .eq('is_deleted', False) \
                .order('evaluation_date', desc=True)

            if filters:
                if filters.get('evaluation_type'):
                    query = query.eq('evaluation_type', filters['evaluation_type'])
                if filters.get('evaluated_resident'):
                    query = query.eq('evaluated_resident', filters['evaluated_resident'])
                if filters.get('evaluator_teacher'):
                    query = query.eq('evaluator_teacher', filters['evaluator_teacher'])
                if filters.get('date_from'):
                    query = query.gte('evaluation_date', filters['date_from'])
                if filters.get('date_to'):
                    query = query.lte('evaluation_date', filters['date_to'])
                if filters.get('department'):
                    query = query.eq('department', filters['department'])

            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"查詢兒科評核記錄失敗: {str(e)}")
            return []

    def insert_pediatric_evaluation(self, data):
        """
        新增一筆兒科評核記錄

        Args:
            data (dict): 評核資料，必須包含：
                - evaluation_type, evaluator_teacher, evaluation_date,
                  evaluated_resident, resident_level
                依 evaluation_type 不同，需包含對應欄位。

        Returns:
            dict | None: 新增成功回傳記錄，失敗回傳 None
        """
        try:
            result = self.client.table('pediatric_evaluations').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"新增兒科評核記錄失敗: {str(e)}")
            return None

    def insert_pediatric_evaluations_batch(self, records):
        """
        批次新增多筆兒科評核記錄（供遷移使用）

        Args:
            records (list[dict]): 評核資料列表

        Returns:
            int: 成功新增的筆數
        """
        try:
            result = self.client.table('pediatric_evaluations').insert(records).execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            print(f"批次新增兒科評核記錄失敗: {str(e)}")
            return 0

    def fetch_pediatric_users(self, user_type=None, active_only=True):
        """
        查詢兒科使用者

        Args:
            user_type (str, optional): 'teacher' | 'resident' | 'admin'
            active_only (bool): 是否僅查詢啟用中的帳號

        Returns:
            list[dict]: 使用者列表
        """
        try:
            query = self.client.table('pediatric_users').select('*')
            if user_type:
                query = query.eq('user_type', user_type)
            if active_only:
                query = query.eq('is_active', True)
            query = query.order('full_name')
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"查詢兒科使用者失敗: {str(e)}")
            return []

    def upsert_pediatric_user(self, data):
        """
        新增或更新兒科使用者

        Args:
            data (dict): 使用者資料，必須包含 username, full_name, user_type

        Returns:
            dict | None: 成功回傳記錄，失敗回傳 None
        """
        try:
            data['updated_at'] = datetime.now().isoformat()
            result = self.client.table('pediatric_users').upsert(
                data, on_conflict='username'
            ).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"新增/更新兒科使用者失敗: {str(e)}")
            return None

    def deactivate_pediatric_user(self, user_id):
        """
        停用兒科使用者帳號

        Args:
            user_id (int): 使用者 ID

        Returns:
            bool: 是否成功
        """
        try:
            self.client.table('pediatric_users').update({
                'is_active': False,
                'updated_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
            return True
        except Exception as e:
            print(f"停用兒科使用者失敗: {str(e)}")
            return False

    def get_active_thresholds(self):
        """
        取得目前作用中的 CCC 門檻設定

        Returns:
            dict: 門檻設定，包含 technical_green_threshold, technical_red_threshold,
                  score_green_threshold, score_red_threshold。
                  若無資料則回傳預設值。
        """
        defaults = {
            'technical_green_threshold': 100.0,
            'technical_red_threshold': 60.0,
            'score_green_threshold': 3.5,
            'score_red_threshold': 2.5,
        }
        try:
            result = self.client.table('pediatric_threshold_settings') \
                .select('*') \
                .eq('is_active', True) \
                .execute()
            if result.data:
                return result.data[0]
            return defaults
        except Exception as e:
            print(f"取得門檻設定失敗: {str(e)}")
            return defaults

    def save_threshold_settings(self, settings, updated_by, notes=''):
        """
        儲存新的門檻設定（停用舊設定，新增新設定）

        Args:
            settings (dict): 必須包含 4 個門檻值
            updated_by (str): 變更者使用者名稱
            notes (str): 變更說明

        Returns:
            bool: 是否成功
        """
        try:
            # 停用目前 active 的設定
            self.client.table('pediatric_threshold_settings') \
                .update({'is_active': False, 'updated_at': datetime.now().isoformat()}) \
                .eq('is_active', True) \
                .execute()

            # 新增新設定
            new_settings = {
                'technical_green_threshold': settings['technical_green_threshold'],
                'technical_red_threshold': settings['technical_red_threshold'],
                'score_green_threshold': settings['score_green_threshold'],
                'score_red_threshold': settings['score_red_threshold'],
                'is_active': True,
                'updated_by': updated_by,
                'notes': notes,
                'effective_from': datetime.now().isoformat(),
            }
            self.client.table('pediatric_threshold_settings').insert(new_settings).execute()
            return True
        except Exception as e:
            print(f"儲存門檻設定失敗: {str(e)}")
            return False

    def log_pediatric_migration(self, record_count, migration_type, status, migrated_by, error_details=None):
        """
        記錄遷移 log

        Args:
            record_count (int): 遷移筆數
            migration_type (str): 'initial' | 'incremental' | 'manual'
            status (str): 'success' | 'partial' | 'failed'
            migrated_by (str): 執行者
            error_details (dict, optional): 錯誤細節
        """
        try:
            self.client.table('pediatric_migration_log').insert({
                'google_sheet_timestamp': datetime.now().isoformat(),
                'record_count': record_count,
                'migration_type': migration_type,
                'status': status,
                'migrated_by': migrated_by,
                'error_details': error_details,
            }).execute()
        except Exception as e:
            print(f"記錄遷移 log 失敗: {str(e)}")

    # =============================================
    # 全科別帳號管理方法
    # =============================================

    def fetch_all_users(self, active_only=True):
        """
        查詢所有使用者（不限 user_type）

        Args:
            active_only (bool): 是否僅查詢啟用中的帳號

        Returns:
            list[dict]: 使用者列表
        """
        try:
            query = self.client.table('pediatric_users').select('*')
            if active_only:
                query = query.eq('is_active', True)
            query = query.order('department').order('full_name')
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"查詢所有使用者失敗: {str(e)}")
            return []

    def batch_upsert_users(self, records):
        """
        批次新增/更新使用者（供 CSV 匯入使用）

        Args:
            records (list[dict]): 使用者資料列表，每筆需含 username, full_name, user_type

        Returns:
            tuple[int, list[str]]: (成功筆數, 錯誤訊息列表)
        """
        success_count = 0
        errors = []
        for rec in records:
            try:
                rec['updated_at'] = datetime.now().isoformat()
                self.client.table('pediatric_users').upsert(
                    rec, on_conflict='username'
                ).execute()
                success_count += 1
            except Exception as e:
                errors.append(f"{rec.get('username', '?')}: {str(e)}")
        return success_count, errors

    # =============================================
    # 研究進度管理方法
    # =============================================

    def fetch_research_progress(self, filters=None):
        """
        查詢研究進度記錄

        Args:
            filters (dict, optional): 過濾條件，支援的 key：
                - resident_name: 住院醫師姓名
                - current_status: 進度狀態
                - supervisor_name: 指導老師
                - department: 科別名稱（用於科別隔離）

        Returns:
            list[dict]: 研究進度列表
        """
        try:
            query = self.client.table('pediatric_research_progress') \
                .select('*') \
                .eq('is_deleted', False) \
                .order('updated_at', desc=True)

            if filters:
                if filters.get('resident_name'):
                    query = query.eq('resident_name', filters['resident_name'])
                if filters.get('current_status'):
                    query = query.eq('current_status', filters['current_status'])
                if filters.get('supervisor_name'):
                    query = query.eq('supervisor_name', filters['supervisor_name'])
                if filters.get('department'):
                    query = query.eq('department', filters['department'])

            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"查詢研究進度失敗: {str(e)}")
            return []

    def insert_research_progress(self, data):
        """
        新增研究進度記錄

        Args:
            data (dict): 研究進度資料

        Returns:
            dict | None: 成功回傳記錄，失敗回傳 None
        """
        try:
            result = self.client.table('pediatric_research_progress').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"新增研究進度失敗: {str(e)}")
            return None

    def update_research_progress(self, research_id, data):
        """
        更新研究進度記錄

        Args:
            research_id (int): 研究 ID
            data (dict): 要更新的欄位

        Returns:
            dict | None: 成功回傳更新後記錄，失敗回傳 None
        """
        try:
            data['updated_at'] = datetime.now().isoformat()
            result = self.client.table('pediatric_research_progress') \
                .update(data) \
                .eq('id', research_id) \
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"更新研究進度失敗: {str(e)}")
            return None

    def delete_research_progress(self, research_id):
        """
        軟刪除研究進度記錄

        Args:
            research_id (int): 研究 ID

        Returns:
            bool: 是否成功
        """
        try:
            self.client.table('pediatric_research_progress').update({
                'is_deleted': True,
                'updated_at': datetime.now().isoformat()
            }).eq('id', research_id).execute()
            return True
        except Exception as e:
            print(f"刪除研究進度失敗: {str(e)}")
            return False

    # =============================================
    # 學習反思管理方法
    # =============================================

    def fetch_learning_reflections(self, filters=None):
        """
        查詢學習反思記錄

        Args:
            filters (dict, optional): 過濾條件，支援的 key：
                - resident_name: 住院醫師姓名
                - reflection_type: 反思類型
                - date_from: 起始日期
                - date_to: 結束日期
                - include_private: 是否包含私人記錄（預設 False）
                - department: 科別名稱（用於科別隔離）

        Returns:
            list[dict]: 學習反思列表
        """
        try:
            query = self.client.table('pediatric_learning_reflections') \
                .select('*') \
                .eq('is_deleted', False) \
                .order('reflection_date', desc=True)

            if filters:
                if filters.get('resident_name'):
                    query = query.eq('resident_name', filters['resident_name'])
                if filters.get('reflection_type'):
                    query = query.eq('reflection_type', filters['reflection_type'])
                if filters.get('date_from'):
                    query = query.gte('reflection_date', filters['date_from'])
                if filters.get('date_to'):
                    query = query.lte('reflection_date', filters['date_to'])
                if not filters.get('include_private', False):
                    query = query.eq('is_private', False)
                if filters.get('department'):
                    query = query.eq('department', filters['department'])

            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"查詢學習反思失敗: {str(e)}")
            return []

    def insert_learning_reflection(self, data):
        """
        新增學習反思記錄

        Args:
            data (dict): 學習反思資料

        Returns:
            dict | None: 成功回傳記錄，失敗回傳 None
        """
        try:
            result = self.client.table('pediatric_learning_reflections').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"新增學習反思失敗: {str(e)}")
            return None

    def update_learning_reflection(self, reflection_id, data):
        """
        更新學習反思記錄

        Args:
            reflection_id (int): 反思 ID
            data (dict): 要更新的欄位

        Returns:
            dict | None: 成功回傳更新後記錄，失敗回傳 None
        """
        try:
            data['updated_at'] = datetime.now().isoformat()
            result = self.client.table('pediatric_learning_reflections') \
                .update(data) \
                .eq('id', reflection_id) \
                .execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"更新學習反思失敗: {str(e)}")
            return None

    def delete_learning_reflection(self, reflection_id):
        """
        軟刪除學習反思記錄

        Args:
            reflection_id (int): 反思 ID

        Returns:
            bool: 是否成功
        """
        try:
            self.client.table('pediatric_learning_reflections').update({
                'is_deleted': True,
                'updated_at': datetime.now().isoformat()
            }).eq('id', reflection_id).execute()
            return True
        except Exception as e:
            print(f"刪除學習反思失敗: {str(e)}")
            return False

    # ==================== 使用者申請管理 ====================

    def fetch_user_applications(self, filters=None):
        """
        查詢使用者申請記錄

        Args:
            filters (dict, optional): 過濾條件，例如：
                {'status': 'pending'}
                {'email': 'user@example.com'}
                {'user_type': 'resident'}

        Returns:
            list: 申請記錄列表，依建立時間降序排列
        """
        try:
            query = self.client.table('user_applications').select('*').eq('is_deleted', False)

            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)

            result = query.order('created_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            st.error(f"查詢申請記錄失敗：{str(e)}")
            return []

    def insert_user_application(self, data):
        """
        新增使用者申請記錄

        Args:
            data (dict): 申請資料，必須包含：
                - full_name, desired_username, password_hash, email, user_type
                - 可選：phone, department, resident_level, supervisor_name, application_reason

        Returns:
            dict: 新建立的申請記錄，或 None（失敗時）
        """
        try:
            # 確保必要欄位存在
            required_fields = ['full_name', 'desired_username', 'password_hash', 'email', 'user_type']
            for field in required_fields:
                if field not in data:
                    st.error(f"缺少必要欄位：{field}")
                    return None

            # 設定預設狀態
            data['status'] = 'pending'
            data['is_deleted'] = False

            result = self.client.table('user_applications').insert(data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"提交申請失敗：{str(e)}")
            return None

    def update_user_application(self, application_id, data):
        """
        更新使用者申請記錄（用於審核）

        Args:
            application_id (int): 申請記錄 ID
            data (dict): 更新資料，例如：
                {'status': 'approved', 'reviewed_by': 'admin', 'reviewed_at': NOW(), 'created_user_id': 123}
                {'status': 'rejected', 'reviewed_by': 'admin', 'reviewed_at': NOW(), 'review_notes': '資料不完整'}

        Returns:
            dict: 更新後的記錄，或 None（失敗時）
        """
        try:
            result = self.client.table('user_applications').update(data).eq('id', application_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"更新申請記錄失敗：{str(e)}")
            return None

    def approve_user_application(self, application_id, reviewer_name, username=None, password=None):
        """
        核准使用者申請並建立帳號

        Args:
            application_id (int): 申請記錄 ID
            reviewer_name (str): 審核者姓名
            username (str, optional): 新使用者的帳號名稱（若為 None 則使用申請人自選帳號）
            password (str, optional): 新使用者的密碼明文（若為 None 則使用申請人自設密碼 hash）

        Returns:
            tuple: (success: bool, message: str, user_id: int or None)
        """
        try:
            # 1. 查詢申請記錄
            app = self.client.table('user_applications').select('*').eq('id', application_id).execute()
            if not app.data:
                return False, "申請記錄不存在", None

            application = app.data[0]

            if application['status'] != 'pending':
                return False, f"申請狀態為 {application['status']}，無法核准", None

            # 2. 決定帳號與密碼 hash
            #    優先使用管理員指定值，否則使用申請人自填值
            final_username = username if username else application.get('desired_username')
            if not final_username:
                return False, "無法取得帳號名稱（申請記錄缺少 desired_username）", None

            if password:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
            else:
                password_hash = application.get('password_hash')
                if not password_hash:
                    return False, "無法取得密碼（申請記錄缺少 password_hash）", None

            user_data = {
                'username': final_username,
                'full_name': application['full_name'],
                'email': application['email'],
                'user_type': application['user_type'],
                'department': application.get('department'),
                'resident_level': application.get('resident_level'),
                'is_active': True,
                'password_hash': password_hash,
                'synced_from_local_auth': False
            }

            new_user = self.upsert_pediatric_user(user_data)
            if not new_user:
                return False, "建立帳號失敗", None

            # 3. 更新申請記錄
            update_data = {
                'status': 'approved',
                'reviewed_by': reviewer_name,
                'reviewed_at': datetime.now().isoformat(),
                'created_user_id': new_user['id']
            }

            self.update_user_application(application_id, update_data)

            return True, f"核准成功，已建立帳號：{username}", new_user['id']

        except Exception as e:
            return False, f"核准過程發生錯誤：{str(e)}", None

    def reject_user_application(self, application_id, reviewer_name, reason):
        """
        拒絕使用者申請

        Args:
            application_id (int): 申請記錄 ID
            reviewer_name (str): 審核者姓名
            reason (str): 拒絕原因

        Returns:
            bool: 是否成功拒絕
        """
        try:
            update_data = {
                'status': 'rejected',
                'reviewed_by': reviewer_name,
                'reviewed_at': datetime.now().isoformat(),
                'review_notes': reason
            }

            result = self.update_user_application(application_id, update_data)
            return result is not None

        except Exception as e:
            st.error(f"拒絕申請失敗：{str(e)}")
            return False