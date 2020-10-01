from flask import Blueprint, request, jsonify, g
from flask_request_validator import (
    GET,
    Param,
    Enum,
    validate_params
)

from util import login_required

def create_qna_endpoints(qna_service, Session):

    qna_app = Blueprint('qna_app', __name__, url_prefix='/api/qnas')

    @qna_app.route('/qna', methods=['POST', 'DELETE'])
    @login_required
    def qna():
        """ question 작성 API

        사용자가 입력한 문의를 데이터베이스에 입력합니다.

        returns :
            200: question 데이터베이스 입력
            400: KEY_ERROR
            500: Exception

        Authors:
            고지원

        History:
            2020-09-26 (고지원): 초기 생성
            2020-09-28 (고지원): 수정
                - delete 메소드 추가
                - 로그인 데코레이터 추가
        """
        session = Session()
        try:
            if request.method == 'POST':

                # 문의 입력을 위한 데이터를 받는다.
                qna_info = {
                    'type_id'    : request.json['type_id'],
                    'user_id'    : g.user_id['user_id'],
                    'product_id' : request.json['product_id'],
                    'content'    : request.json['content'],
                    'is_private' : request.json['is_private']
                }

                qna_service.insert_question(qna_info, session)

                session.commit()

                return jsonify({'message': 'INSERT_SUCCESS'}), 200

            # soft delete 를 위해 question_id 를 쿼리 파라미터로 받는다.
            question_id = request.args.get('question_id')
            qna_service.delete_question(question_id, session)

            session.commit()

            return jsonify({'message': 'DELETE_SUCCESS'}), 200

        except KeyError:
            return jsonify({'message' : 'KEY_ERROR'}), 400

        except Exception as e:
            session.rollback()
            return jsonify({'message' : f'{e}'}), 500

        finally:
            session.close()

    @qna_app.route('', methods=['GET'])
    @validate_params(
        Param('product_id', GET, int, required=True),
    )
    def qnas(*args):
        """ QnA 리스트 전달 API

        product_id 에 따른 QnA 리스트를 표출합니다.

        args:
            product_id: 상품의 pk

        returns :
            200: QnA 리스트
            500: Exception

        Authors:
            고지원

        History:
            2020-09-27 (고지원): 초기 생성
            2020-09-30 (고지원): 파라미터 유효성 검사 추가
        """
        session = Session()
        try:
            qna_info = {}

            # 상품 상세페이지 상품 아이디
            qna_info['product_id'] = args[0]

            body = [{
                'q_id'          : qna.q_id,
                'q_content'     : qna.q_content,
                'q_user'        : qna.login_id,
                'q_type'        : qna.type_name,
                'q_is_answered' : qna.is_answered,
                'q_is_private'  : qna.q_is_private,
                'q_created_at'  : qna.q_created_at,
                'a_id'          : qna.a_id,
                'a_content'     : qna.a_content,
                'a_is_private'  : qna.a_is_private,
                'a_created_at'  : qna.a_created_at
            } for qna in qna_service.get_qnas(qna_info, session)]

            return jsonify(body), 200

        except Exception as e:
            return jsonify({'message' : f'{e}'}), 500

        finally:
            session.close()

    @qna_app.route('/user', methods=['GET'])
    @login_required
    @validate_params(
        Param('product_id', GET, int, required=False),
        Param('is_answered', GET, int, rules=[Enum(0, 1)], required=False),
    )
    def user_qna(*args):
        """ 로그인한 user 의 QnA 리스트 전달 API

        user_id, product_id 에 따른 QnA 리스트를 표출합니다.

        args :
            *args:
            product_id: 상품의 pk
            is_answered: 답변, 미답변 여부 판단위한 파라미터

            g.user_id: 데코레이터에서 넘어온 user 의 pk

        returns :
            200: QnA 리스트
            500: Exception

        Authors:
            고지원

        History:
            2020-09-29 (고지원): 초기 생성
            2020-09-30 (고지원): 파라미터 유효성 검사 추가
        """

        session = Session()
        try:
            qna_info = {}

            # 상품 아이디 (특정 상품의 상세페이지에서 내가 쓴 문의 필터링을 위해)
            qna_info['product_id'] = args[0]

            # 답변 여부
            qna_info['is_answered'] = args[1]

            body = [{
                'q_id'          : qna.q_id,
                'q_content'     : qna.q_content,
                'q_user'        : g.user_id['user_id'],
                'q_type'        : qna.type_name,
                'q_is_answered' : qna.is_answered,
                'q_is_private'  : qna.q_is_private,
                'q_created_at'  : qna.q_created_at,
                'a_id'          : qna.a_id,
                'a_content'     : qna.a_content,
                'a_is_private'  : qna.a_is_private,
                'a_created_at'  : qna.a_created_at
            } for qna in qna_service.get_qnas(qna_info, session)]

            return jsonify(body), 200

        except Exception as e:
            return jsonify({'message': f'{e}'}), 500

        finally:
            session.close()

    return qna_app