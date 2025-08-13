from mindcastlib.configs import TrainingConfig 

cfg = TrainingConfig()











if __name__ == "__main__":
    
    pipe = TrainPipeLIne(
        train_config = cfg.ONLY_SENTIMENT_COMMENTS()
        trian_dir = train_dir,
        eval_dir = eval_dir,
        save_dir = save_dir,
        debug = True)