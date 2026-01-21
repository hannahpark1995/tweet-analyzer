from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import random

app = Flask(__name__)
CORS(app)  # CORS 허용 (프론트엔드와 통신용)

# X Algorithm 가중치 (공개된 알고리즘 기반)
ENGAGEMENT_WEIGHTS = {
    'favorite': 0.5,      # 좋아요
    'reply': 13.5,        # 댓글 (높은 가중치)
    'repost': 7.0,        # 리트윗
    'quote': 8.0,         # 인용
    'click': 0.1,         # 클릭
    'profile_click': 3.0, # 프로필 클릭
    'video_view': 0.01,   # 비디오 뷰
    'photo_expand': 0.005,# 사진 확대
    'share': 10.0,        # 공유
    'dwell': 0.002,       # 체류시간
    'follow': 12.0,       # 팔로우
    'not_interested': -10.0,  # 관심없음
    'block': -15.0,       # 차단
    'mute': -12.0,        # 뮤트
    'report': -20.0       # 신고
}

def extract_tweet_id(url):
    """트윗 URL에서 ID 추출"""
    match = re.search(r'/status/(\d+)', url)
    if match:
        return match.group(1)
    return None

def format_number(num):
    """숫자를 K, M 형식으로 포맷"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

def analyze_with_x_algorithm(metrics):
    """
    X 알고리즘 기반 분석
    Phoenix Scorer의 예측을 시뮬레이션하고 최종 점수 계산
    """
    
    # 실제 메트릭에서 확률 추정
    likes = int(metrics.get('likes', '0').replace('K', '000').replace('M', '000000').replace('.', ''))
    retweets = int(metrics.get('retweets', '0').replace('K', '000').replace('M', '000000').replace('.', ''))
    replies = int(metrics.get('replies', '0').replace('K', '000').replace('M', '000000').replace('.', ''))
    views = int(metrics.get('views', '0').replace('K', '000').replace('M', '000000').replace('.', ''))
    
    # Phoenix Scorer 시뮬레이션 - 각 액션 확률 예측
    total_engagement = likes + retweets + replies
    
    predictions = {
        'favorite': min(likes / max(views, 1) * 100, 100),
        'reply': min(replies / max(views, 1) * 100, 100),
        'repost': min(retweets / max(views, 1) * 100, 100),
        'quote': min((retweets * 0.15) / max(views, 1) * 100, 100),
        'click': min(total_engagement / max(views, 1) * 100, 100),
        'profile_click': min(likes * 0.05 / max(views, 1) * 100, 100),
        'video_view': random.uniform(5, 20),
        'photo_expand': random.uniform(3, 15),
        'share': min(retweets * 0.2 / max(views, 1) * 100, 100),
        'dwell': random.uniform(10, 40),
        'follow': min(likes * 0.01 / max(views, 1) * 100, 100),
        'not_interested': random.uniform(0.1, 2),
        'block': random.uniform(0.01, 0.5),
        'mute': random.uniform(0.01, 0.5),
        'report': random.uniform(0.01, 0.3)
    }
    
    # Weighted Score 계산 (X 알고리즘 공식)
    weighted_score = sum(
        ENGAGEMENT_WEIGHTS[action] * (prob / 100)
        for action, prob in predictions.items()
    )
    
    # 정규화 (0-100 범위)
    normalized_score = max(0, min(100, (weighted_score + 20) * 2.5))
    
    # 알고리즘 인사이트
    insights = {
        'algorithm_score': round(normalized_score, 1),
        'predictions': {k: round(v, 2) for k, v in predictions.items()},
        'top_drivers': [],
        'ranking_factors': {
            'engagement_quality': 'high' if replies > likes * 0.05 else 'medium' if replies > likes * 0.02 else 'low',
            'virality_potential': 'high' if retweets > likes * 0.3 else 'medium' if retweets > likes * 0.15 else 'low',
            'conversation_starter': 'yes' if replies > retweets else 'no',
            'author_diversity_impact': 'neutral'
        },
        'feed_placement_estimate': 'top' if normalized_score > 70 else 'middle' if normalized_score > 40 else 'lower',
        'optimization_suggestions': []
    }
    
    # Top drivers 분석
    weighted_predictions = [
        (action, ENGAGEMENT_WEIGHTS[action] * predictions[action] / 100)
        for action in predictions
    ]
    top_3 = sorted(weighted_predictions, key=lambda x: abs(x[1]), reverse=True)[:3]
    insights['top_drivers'] = [
        {
            'action': action,
            'impact': round(weight, 2),
            'probability': round(predictions[action], 2)
        }
        for action, weight in top_3
    ]
    
    # 최적화 제안
    if replies < likes * 0.03:
        insights['optimization_suggestions'].append({
            'type': 'engagement',
            'message': '질문이나 의견을 요청하여 댓글을 늘리세요 (가중치 13.5x)',
            'priority': 'high'
        })
    
    if retweets < likes * 0.2:
        insights['optimization_suggestions'].append({
            'type': 'virality',
            'message': '공유 가치가 높은 인사이트나 통계를 포함하세요',
            'priority': 'medium'
        })
    
    if predictions['not_interested'] > 1.5:
        insights['optimization_suggestions'].append({
            'type': 'relevance',
            'message': '타겟 오디언스를 더 명확히 하여 부정 신호를 줄이세요',
            'priority': 'medium'
        })
    
    return insights

def scrape_tweet_data(tweet_url):
    """
    트윗 데이터 스크래핑
    
    참고: 실제 프로덕션에서는 다음 중 하나를 사용하세요:
    1. nitter.net (Twitter 프록시)
    2. Apify Twitter Scraper
    3. TwitterAPI.io (유료 대안)
    4. Selenium + Twitter 로그인
    """
    
    tweet_id = extract_tweet_id(tweet_url)
    if not tweet_id:
        return None
    
    # 방법 1: Nitter를 사용한 스크래핑 (무료, 인증 불필요)
    try:
        nitter_url = f"https://nitter.net/i/status/{tweet_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(nitter_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 트윗 컨텐츠
        tweet_content_elem = soup.select_one('.tweet-content')
        tweet_content = tweet_content_elem.get_text(strip=True) if tweet_content_elem else ""
        
        # 작성자 정보
        username_elem = soup.select_one('.username')
        fullname_elem = soup.select_one('.fullname')
        avatar_elem = soup.select_one('.avatar img')
        
        username = username_elem.get_text(strip=True) if username_elem else ""
        fullname = fullname_elem.get_text(strip=True) if fullname_elem else ""
        avatar = avatar_elem['src'] if avatar_elem else ""
        
        # 통계 정보
        stats = soup.select('.icon-container')
        
        comments = 0
        retweets = 0
        likes = 0
        
        for stat in stats:
            stat_text = stat.get_text(strip=True)
            if 'comment' in stat.get('title', '').lower():
                comments = int(re.sub(r'[^\d]', '', stat_text) or 0)
            elif 'retweet' in stat.get('title', '').lower():
                retweets = int(re.sub(r'[^\d]', '', stat_text) or 0)
            elif 'like' in stat.get('title', '').lower():
                likes = int(re.sub(r'[^\d]', '', stat_text) or 0)
        
        # 타임스탬프
        time_elem = soup.select_one('.tweet-date a')
        timestamp = time_elem.get_text(strip=True) if time_elem else ""
        
        # 조회수 추정 (실제 API 없이는 추정치)
        estimated_views = likes * 50  # 대략적인 추정
        
        # 참여율 계산
        total_engagement = comments + retweets + likes
        engagement_rate = (total_engagement / estimated_views * 100) if estimated_views > 0 else 0
        
        return {
            'success': True,
            'data': {
                'content': tweet_content,
                'author': {
                    'name': fullname,
                    'handle': username,
                    'followers': 'N/A',  # Nitter는 팔로워 수를 제공하지 않음
                    'avatar': f"https://nitter.net{avatar}" if avatar else ""
                },
                'metrics': {
                    'views': format_number(estimated_views),
                    'likes': format_number(likes),
                    'retweets': format_number(retweets),
                    'replies': format_number(comments),
                    'bookmarks': format_number(int(likes * 0.1)),  # 추정
                    'quotes': format_number(int(retweets * 0.15))  # 추정
                },
                'engagementRate': f"{engagement_rate:.2f}%",
                'timestamp': timestamp,
                'impressionsPerFollower': 'N/A'
            }
        }
        
    except Exception as e:
        print(f"Scraping error: {e}")
        return None

@app.route('/api/analyze', methods=['POST'])
def analyze_tweet():
    """트윗 분석 API 엔드포인트 - X 알고리즘 분석 포함"""
    try:
        data = request.get_json()
        tweet_url = data.get('url', '')
        
        if not tweet_url:
            return jsonify({
                'success': False,
                'error': '트윗 URL이 필요합니다'
            }), 400
        
        # URL 검증
        if 'twitter.com' not in tweet_url and 'x.com' not in tweet_url:
            return jsonify({
                'success': False,
                'error': '올바른 Twitter/X URL이 아닙니다'
            }), 400
        
        # 트윗 데이터 스크래핑
        result = scrape_tweet_data(tweet_url)
        
        if not result:
            # 스크래핑 실패시 Mock 데이터 반환 (개발용)
            mock_metrics = {
                'views': '150200',
                'likes': '2500',
                'retweets': '456',
                'replies': '89',
                'bookmarks': '234',
                'quotes': '67'
            }
            
            algorithm_analysis = analyze_with_x_algorithm(mock_metrics)
            
            return jsonify({
                'success': True,
                'data': {
                    'content': '트윗 내용을 가져올 수 없습니다. Mock 데이터를 표시합니다.',
                    'author': {
                        'name': 'Sample User',
                        'handle': '@sampleuser',
                        'followers': '10.5K',
                        'avatar': 'https://via.placeholder.com/80/6b7280/ffffff?text=SU'
                    },
                    'metrics': {
                        'views': '150.2K',
                        'likes': '2.5K',
                        'retweets': '456',
                        'replies': '89',
                        'bookmarks': '234',
                        'quotes': '67'
                    },
                    'engagementRate': '2.15%',
                    'timestamp': datetime.now().strftime('%Y년 %m월 %d일'),
                    'impressionsPerFollower': '14.3',
                    'algorithm_analysis': algorithm_analysis,
                    'note': 'This is mock data. Real scraping failed.'
                }
            })
        
        # X 알고리즘 분석 추가
        algorithm_analysis = analyze_with_x_algorithm(result['data']['metrics'])
        result['data']['algorithm_analysis'] = algorithm_analysis
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'서버 오류: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """헬스체크 엔드포인트"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/')
def index():
    """API 정보 페이지"""
    return jsonify({
        'name': 'UnitTX Tweet Analyzer API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/analyze': 'Analyze a tweet by URL',
            'GET /api/health': 'Health check'
        }
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

