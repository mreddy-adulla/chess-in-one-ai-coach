import React from 'react';
import { Chessboard } from 'react-chessboard';

interface ChessBoardProps {
  position: string;
  onPieceDrop: (sourceSquare: string, targetSquare: string) => boolean;
  boardOrientation: 'white' | 'black';
}

const ChessBoard: React.FC<ChessBoardProps> = ({ position, onPieceDrop, boardOrientation }) => {
  return (
    <div className="aspect-square max-w-[600px] mx-auto shadow-xl rounded-lg overflow-hidden">
      <Chessboard
        position={position}
        onPieceDrop={onPieceDrop}
        boardOrientation={boardOrientation}
      />
    </div>
  );
};

export default ChessBoard;