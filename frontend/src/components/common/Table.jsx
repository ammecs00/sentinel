import React from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'
import LoadingSpinner from './LoadingSpinner'

const Table = ({
  columns,
  data,
  loading = false,
  emptyMessage = 'No data available',
  onSort,
  sortColumn,
  sortDirection,
  className = ''
}) => {
  const handleSort = (column) => {
    if (onSort && column.sortable !== false) {
      onSort(column.key)
    }
  }
  
  if (loading) {
    return (
      <div className="table-loading">
        <LoadingSpinner text="Loading data..." />
      </div>
    )
  }
  
  if (!data || data.length === 0) {
    return (
      <div className="table-empty">
        <p>{emptyMessage}</p>
      </div>
    )
  }
  
  return (
    <div className={`table-container ${className}`}>
      <table className="table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                style={{ width: column.width }}
                className={column.sortable !== false ? 'sortable' : ''}
                onClick={() => handleSort(column)}
              >
                <div className="th-content">
                  <span>{column.header}</span>
                  {column.sortable !== false && sortColumn === column.key && (
                    <span className="sort-icon">
                      {sortDirection === 'asc' ? (
                        <ChevronUp size={16} />
                      ) : (
                        <ChevronDown size={16} />
                      )}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={row.id || rowIndex}>
              {columns.map((column) => (
                <td key={column.key}>
                  {column.render
                    ? column.render(row, rowIndex)
                    : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default Table