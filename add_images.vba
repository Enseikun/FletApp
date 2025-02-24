Option Explicit

Private Const DIALOG_TITLE As String = "挿入する画像を選択してください"

' 画像ファイルを選択するプロシージャ
Private Function SelectImageFiles() As Variant
    On Error Resume Next
    
    #If Mac Then
        ' Macのファイル選択ダイアログを表示
        Dim selectedFiles As String
        Dim appleScript As String
        
        appleScript = "try" & vbNewLine & _
                      "    set theFiles to choose file of type " & _
                      "{""public.image""} " & _
                      "with prompt """ & DIALOG_TITLE & """ " & _
                      "with multiple selections allowed" & vbNewLine & _
                      "    set theFilePaths to {}" & vbNewLine & _
                      "    repeat with aFile in theFiles" & vbNewLine & _
                      "        set end of theFilePaths to POSIX path of aFile" & vbNewLine & _
                      "    end repeat" & vbNewLine & _
                      "    set AppleScript's text item delimiters to ASCII character 10" & vbNewLine & _
                      "    return theFilePaths as text" & vbNewLine & _
                      "on error errMsg" & vbNewLine & _
                      "    display dialog errMsg" & vbNewLine & _
                      "    return """" " & vbNewLine & _
                      "end try"
        
        selectedFiles = MacScript(appleScript)
        
        ' デバッグ用：選択結果を表示
        Debug.Print "Selected Files: " & selectedFiles
        
        If selectedFiles = "" Then
            SelectImageFiles = Array()
        Else
            SelectImageFiles = Split(selectedFiles, vbNewLine)
        End If
    #Else
        ' Windowsのファイル選択ダイアログを表示
        With Application.FileDialog(msoFileDialogFilePicker)
            .Filters.Clear
            .Filters.Add "画像ファイル", "*.jpg;*.jpeg;*.png;*.gif;*.bmp", 1
            .Title = DIALOG_TITLE
            .AllowMultiSelect = True
            
            If .Show = -1 Then
                Dim result() As String
                ReDim result(.SelectedItems.Count - 1)
                
                Dim i As Long
                For i = 0 To .SelectedItems.Count - 1
                    result(i) = .SelectedItems(i + 1)
                Next i
                
                SelectImageFiles = result
            Else
                SelectImageFiles = Array()
            End If
        End With
    #End If
End Function

' ファイルパスからファイル名を抽出する関数
Private Function GetFileName(ByVal filePath As String) As String
    #If Mac Then
        ' Macの場合、/で区切られたパスの最後の要素を取得
        Dim parts As Variant
        parts = Split(filePath, "/")
        GetFileName = parts(UBound(parts))
    #Else
        ' Windowsの場合、\で区切られたパスの最後の要素を取得
        Dim parts As Variant
        parts = Split(filePath, "\")
        GetFileName = parts(UBound(parts))
    #End If
End Function

' 最後に挿入された画像の位置を探索する関数
Private Function FindLastCell(ByVal ws As Worksheet) As Range
    dim bottom_row as long
    dim right_col as long

    bottom_row = ws.cells(ws.rows.count, 1).end(xlup).row
    
    ' 偶数行であれば-1
    if bottom_row mod 2 = 0 then
        bottom_row = bottom_row - 1
    end if
    
    right_col = ws.cells(bottom_row, ws.columns.count).end(xltoleft).column
    
    dim c as Range
    set c = ws.cells(bottom_row, right_col)
    
    set FindLastCell = c
End Function

' メインプロシージャ - 画像の挿入を実行
Sub add_images()
    'On Error GoTo ErrorHandler
    
    Dim ws As Worksheet
    Set ws = ActiveSheet
    
    ' 画像ファイルを選択
    Dim selectedFiles As Variant
    selectedFiles = SelectImageFiles()
    
    If UBound(selectedFiles) < 0 Then Exit Sub
    
    'Application.ScreenUpdating = False
    
    ' 最後に画像が挿入されている位置を探索
    Dim currentCell As Range
    Set currentCell = FindLastCell(ws)

    if currentCell.Column >= 9 then
        ' 2行下の最左列に移動
        currentCell.Offset(2, -(currentCell.Column -1)).Select
    else
        if currentCell.Column = 1 then
            if isempty(currentCell.Value) = true then
                ' そのセルで作業開始
                currentCell.Select
            else
                ' 同じ行の1列右に移動
                set currentCell = currentCell.Offset(0, 1)
                currentCell.Select
            end if
        else
            ' 同じ行の1列右に移動
            set currentCell = currentCell.Offset(0, 1)
            currentCell.Select
        end if
    end if

    ' 選択された各画像を挿入
    Dim i As Long
    Dim insertError As Boolean
    Dim fileName As String
    
    i = LBound(selectedFiles)
    Do While i <= UBound(selectedFiles)
        Do While currentCell.Column <= 9 And i <= UBound(selectedFiles) ' I列（9列目）まで
            ' 画像を挿入
            On Error Resume Next
            currentCell.Select
            currentCell.InsertPictureInCell selectedFiles(i)

            With currentCell
                .HorizontalAlignment = xlCenter
                .VerticalAlignment = xlCenter
            End With

            insertError = (Err.Number <> 0)
            On Error GoTo ErrorHandler
            
            If Not insertError Then
                ' ファイル名を取得して次の行に挿入
                fileName = GetFileName(selectedFiles(i))
                With currentCell.Offset(1, 0)
                    .Value = fileName
                    .WrapText = True
                End With
                
                set currentCell = currentCell.Offset(0, 1)
                i = i + 1
            End If
        Loop
        
        ' 2行下の最左列に移動
        set currentCell = currentCell.Offset(2, -(currentCell.Column -1))
    Loop
    
    MsgBox "画像の挿入が完了しました。", vbInformation

CleanUp:
    Application.ScreenUpdating = True
    Exit Sub

ErrorHandler:
    MsgBox "エラーが発生しました: " & vbCrLf & _
           "エラー内容: " & Err.Description, vbCritical
    Resume CleanUp
End Sub







