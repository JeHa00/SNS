import { Link } from "react-router-dom";
import styled from "styled-components/macro";

const PostBox = styled.div`
  width: 350px;
  height: 110px;
  margin: 20px 20px;
  padding: 10px;
  box-shadow: rgba(0, 0, 0, 0.16) 0px 1px 4px;
  //border-bottom: 1px solid #aab1af;
`;

const PostInfo = styled.div`
  font-size: 14px;
  color: #848987;
  span {
    margin-right: 7px;
  }
`;

const Content = styled.div`
  display: block;
  font-size: 15px;
  height: 70px;
  margin-bottom: 6px;
  text-overflow: ellipsis;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  line-height: 18px;
`;

function Post() {
  return (
    <PostBox>
      <Content>
        아카나 사료중에서 그래스랜드와 프레이리가 있는데, 이들 사료는 고단백
        사료로 프리미엄 라인에 속하는 사료입니다. 다만 가격이 조금 비싸서 어떤걸
        살지 매우고민이 되는 상황입니다. 결국 원래 먹이던걸 사려고 결정을 했고
        단테는 너무 식탐이 커서 그대로 기호성이 낮은 사료를 먹일 예정입니다
      </Content>
      <PostInfo>
        <span>user_name</span>
        <span>time</span>
        <span>하트 87</span>
      </PostInfo>
    </PostBox>
  );
}

export default Post;
