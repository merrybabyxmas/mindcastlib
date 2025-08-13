정신건강 프로젝트 패키지 


1. analysis pipeline : 기존의 정신건강 파이프라인 (뉴스 감정 분류 , 토픽 분류 , summarize) 수행
   - Done
         1. 모듈마다 원하는 target 설정가능(title, comments)
         2. 모듈마다 원하는 model 설정가능(base model, 직접 학습시킨 모델...etc)
         3. config pre-set 제공 (config customizing 도 가능)
         4. 날짜 조건으로 데이터 읽기 기능 제공
      - TODO
          1. modelConfig 프리셋 추가 (현재는 default model preset)
          2. 실시간 모니터링 기능 추가 ( self.monitoring = True)
          3. 그 외 기능 추가 (e.g. 제목 - 댓글 간의 관계)
       
2. train pipeline : 정신건강 학습 파이프라인 (뉴스 감정 분류 , 토픽 분류 , summarize) 수행
      - TODO
          1. 학습 방법 option으로 제공 (e.g. Literal["lastlayerFT", "LoRA", "train-freeFT"])
          2. 학습 모니터링 기능 추가 (e.g. tensorboard)
          3. 그 외 기능 추가 (e.g. baseModel과의 성능 비교 PipeLine)
       

3. debug pipeline : DB측 과의 연결성을 위한 파이프라인
       - TODO
          1. 추론 시간 모니터링
          2. 저장 용량 모니터링
          3. 각 config 별 FILE I/O 시간 및 data & GPU/CPU usage grid comparison 기능  
       
