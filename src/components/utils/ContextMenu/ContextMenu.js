import React, { useCallback, useEffect, useState } from 'react';
import { Popover } from 'react-bootstrap';
import "./ContextMenu.css";

const ContextMenu = ({ show, menuOptions, onHide, position, containerRef }) => {
  const [adjustedPosition, setAdjustedPosition] = useState({ x: position?.x, y: position?.y });

  const contextMenuPosition = useCallback(() => {
    const container = containerRef?.current;
    const containerRect = container ? container.getBoundingClientRect() : null;
    const containerHeight = containerRect?.height;
    const containerWidth = containerRect?.width;

    // Adjust the position of the context menu if it exceeds the container boundaries
    let newPosition = { ...position };
    const windowWidth = window.innerWidth;
    const windowHeight = window.innerHeight;

    if (containerWidth && containerHeight) {
      // If the menu goes out of the right edge
      if (newPosition.x + 150 > containerWidth) {
        newPosition.x = containerWidth - 165;
      }

      // If the menu goes out of the bottom edge
      if (newPosition.y + 150 > containerHeight) {
        newPosition.y = containerHeight - 170;
      }
    } else {
      if (newPosition.x + 150 > windowWidth) {
        newPosition.x = windowWidth - 165;
      }
      if (newPosition.y + 165 > windowHeight) {
        newPosition.y = windowHeight - 200;
      }
    }

    setAdjustedPosition(newPosition);
  }, [containerRef, position]);

  useEffect(() => {
    window.addEventListener('resize', contextMenuPosition);
    contextMenuPosition();

    const handleClickOutside = (e) => {
      if (show && !e.target.closest('.popover')) onHide(false);
    };

    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      window.removeEventListener('resize', contextMenuPosition);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [position, containerRef, show, onHide, contextMenuPosition]);

  if (!show) return null;

  return (
    <Popover
      className="context-menu-popover border-0 p-0"
      style={{
        position: 'absolute',
        left: adjustedPosition.x,
        top: adjustedPosition.y,
        zIndex: 99999,
        width: "fit-content"
      }}
    >
      <Popover.Body className="p-0 w-100" style={{ border: "1px solid black", borderRadius: "5px" }}>
        <div className="list-group list-group-flush">
          {menuOptions?.map((option, index) => (
            <button
              key={index}
              id={option?.title}
              style={{ borderRadius: "5px", padding: "4px 18px" }}
              className="list-group-item list-group-item-action border-0 d-flex align-items-center"
              onClick={() => { option?.action(); onHide(false); }}
              disabled={!option?.action}
            >
              <span className="me-2" style={{ fontSize: "16px" }}>{option?.icon}</span>
              {option?.title}
            </button>
          ))}
        </div>
      </Popover.Body>
    </Popover>
  );
};

export default ContextMenu;
